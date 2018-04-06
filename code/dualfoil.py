##Author: Dan Steingart
##Date Started: 2015-04-01
##Notes: Wrapper Script for DualFoil 5.1

from pithy import *
from commands import getoutput as go
import subprocess
import atexit
import os
from glob import glob
import signal
from StringIO import StringIO
import pandas as pd
from scipy.interpolate import interp1d
import filecmp
from scipy.interpolate import interp2d as i2d

class dualfoil():
    def __init__(self,name,dfdir="/dualfoil5/df5.1/"):
        self.user = name
        self.df = dfdir
        self.dualbase = dfdir+"dualfoil5.in"
        self.parts = self.readin()
        self.cycles = self.getcycles()
   
    #thanks stack https://stackoverflow.com/a/24937408
    def in_ipynb(self):
        try:
            cfg = get_ipython().config 
            return True
        except NameError:
            return False

    def clear_cycles(self): self.cycles = ""

    def set_ocv(self,mins): 
        self.cycles += "0 %f 1 2.0 4.70\n" % mins
    
    def set_current(self,cur,mins,minv=2.0,maxv=4.7): 
        self.cycles += "%f %f 1 %f %f\n" % (cur,mins,minv,maxv)

    # def set_potential(self,pot,mins,minv=2.0,maxv=4.7): 
    #     self.cycles += "%f %f 0 %f %f\n" % (pot,mins,minv,maxv)

    def readin(self):
        data = open(self.dualbase).read()
        parts = {}
        lines = data.split("\n")
        for l in lines[0:74]:
            p = l.split("!")
            try:
                key = p[1].split(",")[0].strip().split(" ")[0]
                parts[key] = p[0]
            except Exception as err:
                print err
        go("mkdir df_"+self.user+"/files/")
        go("cp -n "+self.df+"/* df_"+self.user+"/")
        return parts
    
    def getcycles(self):
        data = open(self.dualbase).read()
        lines = data.split("\n")
        return lines[74]
    
    def writeOut(self,endless=False):
        self.cycles = self.cycles.strip()
        data = open(self.dualbase).read()
        self.parts['lcurs'] = str(len(self.cycles.split('\n')))
        if endless: self.parts['lcurs'] = 101
        lines = data.split("\n")
        pull = self.cycles.replace('\n', 'd', 101).find('\n')
        if pull != -1:
            self.cycles = self.cycles[0:pull]
            print "too many changes, going endless"
            self.parts['lcurs'] = 101
    
        fn =  "df_"+self.user+"/dualfoil5.in"
        fnc =  "df_"+self.user+"/lastin"
        out = ""
        for l in lines[0:74]:
            p = l.split("!")
            key = p[1].split(",")[0].strip().split(" ")[0]
            out += str(self.parts[key]) + " ! "+p[1]+"\n"
        out += self.cycles +"\n"
        try:
            fil = open(fn).read()
            if fil == out:
                doo = "foo"
                #print "same as the old file, not changing"
            else:
                #print "changed!  writing"
                open(fn,"w").write(out)
        except:    
            open(fn,"w").write(out)
    
    def runDualFoil(self,debug = False,filename=None,force=False,output=False):
        hh="""   Time     Util N  Util P  Cell Pot   Uocp      Curr      Temp   heatgen
   (min)       x       y      (V)       (V)      (A/m2)    (C)    (W/m2)"""

        try:
            fni =  "df_"+self.user+"/dualfoil5.in"
            fno =  "df_"+self.user+"/dualfoil5.out"
            ti = os.path.getmtime(fni)
            to = os.path.getmtime(fno)
        except:
            #if something farts above, just make it so we have to 
            #run the simulation
            ti = 1
            to = 0
        
        runs = glob("df_%s/files/*/dualfoil5.in" % self.user)
        same = None
        for run in runs:
            if filecmp.cmp(fni,run) == True and force == False:
                same = run
                rd = run.replace("dualfoil5.in","")
                go("cp %s/*.out df_%s/" % (rd,self.user))
                if debug: print "same as %s" % run
                if debug: print "not running, pulling previous run"
                return 0
        
        if debug: 
            print "Time Difference Between last input and output:", ti-to," s"

        if ti > to or force:
            if debug: print "input older than output: analysis is not current: running simulation"
            
            a = go("rm df_"+self.user+"/*.out")
            if debug: print a
            #b = go("cd df_"+self.user+";./dualfoil")
            comm = "cd df_"+self.user+";./dualfoil"
            b = subprocess.Popen(comm,shell=True)
            if output: print hh
            while b.poll() != 0:
                time.sleep(1)
                if output: print go("tail -n 1 %s" % fno)
            print ""
            if debug: print b
            c = go("mkdir "+"df_"+self.user+"/files/")
            if debug: print c
        
        
            if filename == None: filename = "run_"+str(time.time())
            dd = {}
            dd['user'] = self.user
            dd['name'] = "df_"+self.user+"/files/"+filename
            d = go("mkdir -p %(name)s; cp df_%(user)s/*.out %(name)s/; cp df_%(user)s/*.in %(name)s/" % dd) 
            if debug: print d
        else: 
            doo = "foo"
            if debug: 
                print "input younger that output: analysis is current: no need to run simulation"
    
    def readProfiles(self,filename=None):
        if filename == None:
            fn = "df_%s/profiles.out" % self.user
        f = open(fn).read()

        Header = "Distance (um),C Elec (mol/m3),C Sol Surf (x/y),Liq Pot (V),Solid Pot (V),Liq Cur (A/m^2),i main (A/m^2),j side 1 (A/m^2),j side 2 (A/m^2), j side 3 (A/m^2)"
        
        #print f
        data = f.split("\n  \n  \n")
        
        profiles = {}
        
        for i in range(len(data)):
            try:
                d = data[i].split("\n")
                step_time = float(d[3].split("=")[-1].replace("min",""))
                profs = Header+"\n"
                for l in d[4:]: profs += l+"\n"
                df = pd.read_csv(StringIO(profs))
                profiles[step_time] = df
            except: weare = "moving on"
        return profiles

    def readOutput(self,showraw = False,debug = False,filename=None):
        #these are the values we care about
        header = ['t','nutil','putil','vcell',"ocp",'i','T','Q']

        #If we don't ask for a specific run, see if there's a recent run
        if filename == None:
            try: data = open("df_"+self.user+"/dualfoil5.out").read()
            #if there's not a recent run, no biggie.
            except: data = ""
        else:
            try:
                data = open("df_"+self.user+"/files/dualfoil_"+filename+".out").read()
            except:
                print "going to video tape"
                print filename
                data = open(filename).read()
    
        raw = data
        if showraw: print raw
        start = data.find("DUAL INSERTION CELL")
        rest = data
        data = data[start:]
        data = data.split("\n")
        out = {}
        out['se'] = []
        out['sp'] = []
        out['sq'] = []
        
        show
        
        for h in header:
            out[h] = []
        try:
            data.pop(0)
            data.pop(0)
            data.pop(0)
            data.pop(0)
        except:
            print "can't pop"
        for d in data:
            p = d.strip().split(",")   
            for i in range(0,len(header)):
                try:
                    out[header[i]].append(float(p[i]))
                except Exception as Err:
                    if debug: print Err
                    nope = True 
        for h in header:
            out[h] = array(out[h])
    
    
        #get specific energy
        rawe = raw
        while rawe.find("specific energy segment") > -1:
            rawe = rawe[rawe.find("specific energy segment"):]
            sestart = rawe.find("specific energy segment")
            seend = rawe.find("W-h/kg")
            try:
                out['se'].append(float(rawe[sestart:seend].split("=")[1]))
            except Exception as err: 
                out['se'].append("-1")
                #out['se'] = -1
            rawe = rawe[5:]

        rawp = raw
        while rawp.find("specific power segment") > -1:
            rawp = rawp[rawp.find("specific power segment"):]
            spstart = rawp.find("specific power segment")
            spend = rawp.find("W/kg")
            try:
               out['sp'].append(float(rawp[spstart:spend].split("=")[1]))
            except:
              out['sp'].append(-1)
            rawp = rawp[5:]        

        rawq = raw
        while rawq.find("total heat") > -1:
            rawq = rawq[rawq.find("total heat"):]
            spstart = rawq.find("total heat")
            spend = rawq.find("W")
            try:
               out['sq'].append(float(rawq[spstart:spend].split("=")[1]))
            except:
              out['sq'].append(-1)
            rawq = rawq[5:]        
        
        
        out['raw'] = raw
        return out

    def surfplot(self,profs,xval,yval,dpi=150):
            times = profs.keys()
            times.sort()
            app = []

            for t in times:
                x = profs[t][xval]
                y = profs[t][yval]
                x = array(x)
                y = array(y)
                app.append(y)
                
    
            t_change = [0]
            for f in self.cycles.split("\n"):
                try:
                    p = array(f.split(" ")).astype(float)
                    if p[2] == 1: 
                        t_change.append(t_change[-1]+p[1])
                except: "whoops"

            
            app = array(app)
            times = array(times)
            z = i2d(x,times,app)
            xx = linspace(0,max(x),1000)
            yy = linspace(0,max(times),1000)
            zz = z(xx,yy)
            
            
            imshow(zz,
                    extent=(0,max(x),max(times),0),
                    aspect='auto',
                    cmap=cm.jet)
            
            for t in t_change: axhline(t,color='gray',alpha=.5,linewidth=1)
            colorbar()
            title(yval)
            xlabel("Position ($\mu m$)")
            ylabel("Time (minutes)")
            if self.in_ipynb(): show()
            else: showme(dpi=dpi)
            clf()

    def ivtplot(self,dpi=150,ir_emph=False):
        data = self.readOutput()
        #plot stuff
        subplot(2,1,1)
        plot(data['t'],data['vcell'],'k',label="loaded potential")
        plot(data['t'],data['ocp'],'grey',label='eq potential',linewidth=.5)
        if ir_emph: fill_between(data['t'],data['vcell'],data['ocp'],where=data['i']!=0,color='r',alpha=.5)
        xticks([])
        ylabel("Potential (V)")
        legend(loc='best',fontsize=8)

        subplot(2,1,2)
        xlabel("Time (m)")
        plot(data['t'],data['i'],'k')
        
        
        ylabel("Current ($mA/cm^2$)")
        xlabel("Time (m)")

        if self.in_ipynb(): show()
        else: showme(dpi=dpi)
        clf()


if __name__ == "__main__":
    
    dpi = 300 #pretty pictures
    
    #instantiate simulator
    df = dualfoil("user")
    
    #Set up electric test
    df.clear_cycles()
    for i in range(1):
        df.set_ocv(10) #set ocv for 3 minutes
        df.set_current(30,40) #discharge at 30 A/m^2 for 40 minutes
        df.set_ocv(10) #set ocv for 10 minutes
        df.set_current(-30,41) #charge for 40 minutes @ 30 A/m^3
    
    
    # uncomment to see available keys
    # pp = df.parts.keys()
    # pp.sort()
    # for p in pp: print p,df.parts[p]
    
    
    #specify cell properties
    df.parts['ep1'] = .3 #set 
    df.parts['h1'] = 150e-6
    df.parts['h3'] = 150e-6
    
    #write changes to disk and run simulation
    df.writeOut()
    df.runDualFoil(debug=False,force=True,output=True)
    data = df.readOutput() #output of ivt in dataframe format
    
    
    ##short ivt data
    df.ivtplot(ir_emph=True)
    
    ##make surface plots
    profs = df.readProfiles()
    vals = profs[profs.keys()[0]].keys()
    for j in ['Distance','j','Pot']:
        vals = [i for i in vals if i.find(j) == -1]
    
    xxx = 'Distance (um)'
    for v in vals: df.surfplot(profs,xxx,v,dpi=dpi)
    
    print data['se']