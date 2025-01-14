# Many of the functions in utils.py use variables defined within FDS.ipynb,
#  so those function can only be used from within that notebook by running the following:
#  %run -i code/utils.py

import pandas as pd
import numpy as np
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time
import os.path

from PIL import Image
from mpl_toolkits import mplot3d
from matplotlib import cm
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from os import path
from lsf import LSFMonitor
from slurm import SlurmMonitor
from slread import slread
import fileinput
import sys
from collections import deque

from matplotlib.pyplot import figure
from matplotlib.colors import ListedColormap
#from sklearn.preprocessing import MinMaxScaler
from pylab import *

cmap_brg = plt.cm.get_cmap('brg', 256)
clist_rg = cmap_brg(np.linspace(0.5, 1, 128))
cmap_rg = ListedColormap(clist_rg)

###################################################################################################
# Function that reads the elevation file

def read_elevation(name_of_file):
    Mst = pd.read_csv(name_of_file)
    Mst['x'] = Mst['x']-Mst['x'].min()
    Mst['y'] = Mst['y']-Mst['y'].min()
    Mst['Elevation'] = Mst['Elevation']-Mst['Elevation'].min()
    return Mst

# Writing the FDS file

def write_fds_file(T_begin, T_end, DT, PC, Nmx, Nmy, Nmz, Hrr, Child):
    global fds
    global job_log
    global foldername
    global filename
    global Dx
    global Nx
    global Dy
    global Ny
    global Dz
    global Nz
    global Dx
    global Nx
    global Rx
    global Ry
    global Rz
    
    NFRAMES  = int(2*(T_end-T_begin))

    fds_filename = f"{PATH}/simulations/{foldername}/{Child}/{filename}"
    fds     = open(fds_filename, 'w')

    ############################################################
    # Drawing the area of the region of interest and cropping ot
    draw_rectangle(Image_name,1000,1000,Min_x,Max_x,Min_y,Max_y,f"{PATH}/simulations/{foldername}/{Child}/Whole{Child}.png",'b')
    # Cropping the region from the Big Region
    crop_rectangle(Image_name,1000,1000,Min_x,Max_x,Min_y,Max_y,f"{PATH}/simulations/{foldername}/{Child}/{Child}.png")
    ############################################################
    DX  = (Max_x-Min_x)/Nmx
    DY  = (Max_y-Min_y)/Nmy
    DZ  = (Max_z-Min_z)/Nmz

    fds.write(f"&HEAD CHID='{Child}', TITLE='Simulation of Chimney Tops fire' /\n\n")
    Nx = math.ceil(DX/R)     # Number of cells in x-direction first mesh (Resolution)
    Ny = math.ceil(DY/R)     # Number of cells in y-direction first mesh (Resolution)
    Nz = math.ceil(DZ/R)     # Number of cells in z-direction first mesh (Resolution)
    
    Rx = DX/Nx
    Ry = DY/Ny 
    Rz = DZ/Nz

    fds.write(f"&MESH IJK={Nx},{Ny},{Nz}, XB={Min_x},{Min_x+DX},{Min_y},{Min_y+DY},{Min_z},{Min_z+DZ}, MULT_ID='mesh' / \n")
    fds.write(f"&MULT ID='mesh', DX={DX}, DY={DY}, DZ={DZ}, I_LOWER=0, I_UPPER={Nmx-1}, J_LOWER=0, J_UPPER={Nmy-1}, K_UPPER={Nmz-1} /  \n\n")
    fds.write("&MISC TMPA=30., TERRAIN_CASE=.TRUE., TERRAIN_IMAGE='Region1.png', VERBOSE=.TRUE., RESTART=.FALSE., PROJECTION=.TRUE., IBLANK_SMV=.FALSE.   /\n")
    
    fds.write(f"&TIME T_BEGIN = {T_begin}, T_END = {T_end} / \n\n")

    fds.write(f"&DUMP NFRAMES={NFRAMES}, DT_PART=100., CFL_FILE=.TRUE., DT_PL3D={T_end}, UVW_TIMER(1)={UVW_Timer} /  \n")
    
    fds.write("&WIND DIRECTION=135., SPEED=5., SPONGE_CELLS=0, STRATIFICATION=.FALSE. /\n\n")


    fds.write(f"&SLCF XB={Min_x},{Max_x},{Min_y},{Max_y},{Min_z},{Max_z}, QUANTITY='HRRPUV', CELL_CENTERED=.TRUE. /  \n\n")
    
    elevation_file = f'{PATH}/data/Elevations_Files/gatlinburg_res_1x1.elv'
    resolution     = R
    quantity       = 'HRRPUV'
    buffer         = 0.5
    border         = [Min_x,Max_x,Min_y,Max_y]
    device_file    = f'{PATH}/simulations/{foldername}/{Child}/devices_{quantity}.dev'
    setting_devices(elevation_file,resolution,quantity,buffer,border,device_file)
    fds.write(f"&CATF OTHER_FILES='devices_{quantity}.dev' / \n\n")
    
    
    fds.write("&RADI KAPPA0=0 / \n\n")
    
    for k in Hrr.index:
        fds.write(f"&SURF ID='FIRE{k}', HRRPUA={math.ceil(Hrr['hrr'][k])}., COLOR='ORANGE', RAMP_Q='fire' /\n")
    
    fds.write(f"\n")
    
    fds.write(f"&RAMP ID='fire', T= {int(T_begin)}., F=0. /\n")
    fds.write(f"&RAMP ID='fire', T= {int(T_begin+1)}., F=1. /\n")
    fds.write(f"&RAMP ID='fire', T= {int(T_begin+rampa_time)}., F=1. /\n")
    fds.write(f"&RAMP ID='fire', T= {int(T_begin+rampa_time+1)}., F=0. /\n\n")

    #fds.write("&SLCF PBZ={Max_z}., AGL_SLICE=1., QUANTITY='VELOCITY', VECTOR=.TRUE. /\n\n")

    fds.write("&VENT MB='XMIN', SURF_ID='OPEN' /  \n")
    fds.write("&VENT MB='XMAX', SURF_ID='OPEN' /  \n")
    fds.write("&VENT MB='YMIN', SURF_ID='OPEN' /  \n")
    fds.write("&VENT MB='YMAX', SURF_ID='OPEN' /  \n")
    fds.write("&VENT MB='ZMAX', SURF_ID='OPEN' /  \n\n")
                 
                                
    fds.write("&REAC FUEL='CELLULOSE', C=6, H=10, O=5, SOOT_YIELD=0.005 / \n\n")
    fds.write("&SPEC ID='WATER VAPOR' / \n\n")

    fds.write("&SURF ID                        = 'grass' \n")
    fds.write("      MATL_ID(1,1:2)            = 'GENERIC VEGETATION','MOISTURE'\n")
    fds.write("      MATL_MASS_FRACTION(1,1:2) = 0.937,0.063\n")
    fds.write("      THICKNESS                 = 0.0002\n")
    fds.write("      LENGTH                    = 0.21\n")
    fds.write("      HEAT_TRANSFER_COEFFICIENT = 30.\n")
    fds.write("      GEOMETRY                  = 'CYLINDRICAL' /\n\n")

    fds.write("&SURF ID                        = 'needles' \n")
    fds.write("      MATL_ID(1,1:2)            = 'GENERIC VEGETATION','MOISTURE'\n")
    fds.write("      MATL_MASS_FRACTION(1,1:2) = 0.95,0.05\n")
    fds.write("      THICKNESS                 = 0.02\n")
    fds.write("      LENGTH                    = 0.21\n")
    fds.write("      HEAT_TRANSFER_COEFFICIENT = 30.\n")
    fds.write("      GEOMETRY                  = 'CYLINDRICAL' /\n\n")

    fds.write("&MATL ID = 'GENERIC VEGETATION' \n")
    fds.write("      DENSITY = 500.\n")
    fds.write("      CONDUCTIVITY = 0.1\n")
    fds.write("      SPECIFIC_HEAT= 1.5\n")
    fds.write("      REFERENCE_TEMPERATURE = 200\n")
    fds.write("      PYROLYSIS_RANGE = 30.\n")
    fds.write("      NU_MATL = 0.2\n")
    fds.write("      NU_SPEC = 0.8 \n")
    fds.write("      SPEC_ID = 'CELLULOSE'\n")
    fds.write("      HEAT_OF_COMBUSTION = 15600.\n")
    fds.write("      HEAT_OF_REACTION = 418.\n")
    fds.write("      MATL_ID  = 'CHAR' /\n\n")

    fds.write("&MATL ID = 'MOISTURE' \n")
    fds.write("      DENSITY = 1000.\n")
    fds.write("      CONDUCTIVITY = 0.1\n")
    fds.write("      SPECIFIC_HEAT= 4.184\n")
    fds.write("      REFERENCE_TEMPERATURE = 100.\n")
    fds.write("      PYROLYSIS_RANGE = 10.\n")
    fds.write("      NU_SPEC = 1.0 \n")
    fds.write("      SPEC_ID = 'WATER VAPOR'\n")
    fds.write("      HEAT_OF_REACTION = 2500./\n\n")

    fds.write("&MATL ID = 'CHAR'\n")
    fds.write("      DENSITY  = 100.\n")
    fds.write("      CONDUCTIVITY = 0.1 \n")
    fds.write("      SPECIFIC_HEAT = 1.0 / \n\n")

    fds.write("&MATL ID='DIRT'\n")
    fds.write("      CONDUCTIVITY = 0.25\n")
    fds.write("      SPECIFIC_HEAT = 2.\n")
    fds.write("     DENSITY = 1300. /\n\n")

    fds.write("&PART ID='foliage', DRAG_COEFFICIENT=1.0, SURF_ID='needles', SAMPLING_FACTOR=5,\n")
    fds.write("      QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE DIAMETER', STATIC=.TRUE., COLOR='GREEN' / \n\n")

    fds.write("&PART ID='grass', DRAG_COEFFICIENT=1.0, SURF_ID='grass', SAMPLING_FACTOR=958,\n")
    fds.write("      QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE DIAMETER', STATIC=.TRUE., COLOR='BROWN' /\n\n")

    fds.write("&SURF ID = 'surf1', RGB = 122,117,48, MATL_ID='DIRT', THICKNESS=0.2, PART_ID='grass', PARTICLE_SURFACE_DENSITY=1.0 / \n")
    fds.write("&SURF ID = 'surf2', RGB = 0,100,0, MATL_ID='DIRT', THICKNESS=0.2 / \n\n")
    
    ###################################################################################################################################
    # Writing the obstacles
    Mst_fire    = Mst.loc[Hrr.index.values]                              # Obstacles on fire
    
    indice2 = [i for i in Mst.index.values if i not in Hrr.index.values] # Index of obstacles on fire 
    
    Mst_no_fire = Mst.loc[indice2]                                       # Obstacles with no fire
    
    # Writing the location of the fire
    for ind in Mst_fire.index:

        fds.write(f"&OBST XB={Mst_fire['x'][ind]},{Mst_fire['x'][ind]+Ro},{Mst_fire['y'][ind]},{Mst_fire['y'][ind]+Ro},{Min_z},{Mst_fire['z'][ind]} SURF_IDS='FIRE{ind}','surf1' /\n")
        
    for ind in Mst_no_fire.index:

        fds.write(f"&OBST XB={Mst_no_fire['x'][ind]},{Mst_no_fire['x'][ind]+Ro},{Mst_no_fire['y'][ind]},{Mst_no_fire['y'][ind]+Ro},{Min_z},{Mst_no_fire['z'][ind]} SURF_ID='surf1' /\n")        
    
########################################################################################################################################
    
    
    fds.close()
    
###############################################################################################################

def restart_fds_file(T_begin, T_end, DT, PC, Nmx, Nmy, Nmz, Child):
    global fds
    global job_log
    global foldername
    global filename
    global Dx
    global Nx
    global Dy
    global Ny
    global Dz
    global Nz
    global Dx
    global Nx
    global Rx
    global Ry
    global Rz
    global rampa_time
                  
    NFRAMES  = int(2*(T_end-T_begin))

    

    fds_filename = f"{filename}"
    fds     = open(fds_filename, 'w')

    ############################################################
    # Drawing the area of the region of interest and cropping it
    ############################################################
    # Drawing the area of the region of interest and cropping ot
    draw_rectangle(f"{PATH}/simulations/{foldername}/{Child_pr}/Whole{Child_pr}.png",1000,1000,Min_x,Max_x,Min_y,Max_y,f"{PATH}/simulations/{foldername}/{Child}/Whole{Child}.png",'b')
    # Cropping the region from the Big Region
    crop_rectangle(Image_name,1000,1000,Min_x,Max_x,Min_y,Max_y,f"{PATH}/simulations/{foldername}/{Child}/{Child}.png")
    

   
    DX  = (Max_x-Min_x)/Nmx
    DY  = (Max_y-Min_y)/Nmy
    DZ  = (Max_z-Min_z)/Nmz

    fds.write(f"&HEAD CHID='{Child}', TITLE='Simulation of Chimney Tops fire' /\n\n")
    Nx = math.ceil(DX/R)     # Number of cells in x-direction first mesh (Resolution)
    Ny = math.ceil(DY/R)     # Number of cells in y-direction first mesh (Resolution)
    Nz = math.ceil(DZ/R)     # Number of cells in z-direction first mesh (Resolution)

    fds.write(f"&MESH IJK={Nx},{Ny},{Nz}, XB={Min_x},{Min_x+DX},{Min_y},{Min_y+DY},{Min_z},{Min_z+DZ}, MULT_ID='mesh' / \n")
    fds.write(f"&MULT ID='mesh', DX={DX}, DY={DY}, DZ={DZ}, I_LOWER=0, I_UPPER={Nmx-1}, J_LOWER=0, J_UPPER={Nmy-1}, K_UPPER={Nmz-1} /  \n\n")
    fds.write(f"&MISC TMPA=30., TERRAIN_CASE=.TRUE., TERRAIN_IMAGE='{Child}.png', VERBOSE=.TRUE., RESTART=.FALSE., PROJECTION=.TRUE.  /\n")
    
    fds.write(f"&TIME T_BEGIN = {T_begin}, T_END = {T_end} / \n\n")

    fds.write(f"&DUMP NFRAMES={NFRAMES}, DT_PART=100., CFL_FILE=.TRUE., DT_PL3D={DTT} /  \n")

    fds.write("&WIND DIRECTION=135., SPEED=5., SPONGE_CELLS=0, STRATIFICATION=.FALSE. /\n\n")
                  
    fds.write(f"&SLCF XB={Min_x},{Max_x},{Min_y},{Max_y},{Min_z},{Max_z}, QUANTITY='HRRPUV', CELL_CENTERED=.TRUE. /  \n\n")
    fds.write(f"&CATF OTHER_FILES='../{Child_pr}/{init_file}' / \n\n")
  
    fds.write(f"\n")
                  
    elevation_file = f'{PATH}/data/Elevations_Files/gatlinburg_res_1x1.elv'
    resolution     = R
    quantity       = 'HRRPUV'
    buffer         = 0.5
    border         = [Min_x,Max_x,Min_y,Max_y]
    device_file    = f'{PATH}/simulations/{foldername}/{Child}/devices_{quantity}.dev'
    setting_devices(elevation_file,resolution,quantity,buffer,border,device_file)
    fds.write(f"&CATF OTHER_FILES='devices_{quantity}.dev' / \n\n")
    
    fds.write(f"&RAMP ID='fire', T= {int(T_begin)}, F=1. /\n")
    if (DTT < 1.0):
        fds.write(f"&RAMP ID='fire', T= {T_begin+DTT}, F=1. /\n")
        Run_Region = False
    fds.write(f"&RAMP ID='fire', T= {float(T_begin+rampa_time/2)}, F=1. /\n")
    fds.write(f"&RAMP ID='fire', T= {float(T_begin+rampa_time)}, F=0. /\n")


    fds.write("&VENT MB='XMIN', SURF_ID='OPEN' /  \n")
    fds.write("&VENT MB='XMAX', SURF_ID='OPEN' /  \n")
    fds.write("&VENT MB='YMIN', SURF_ID='OPEN' /  \n")
    fds.write("&VENT MB='YMAX', SURF_ID='OPEN' /  \n")
    fds.write("&VENT MB='ZMAX', SURF_ID='OPEN' /  \n\n")
    fds.write("&REAC FUEL='CELLULOSE', C=6, H=10, O=5, SOOT_YIELD=0.005 / \n\n")
    fds.write("&SPEC ID='WATER VAPOR' / \n\n")

    fds.write("&SURF ID                        = 'grass' \n")
    fds.write("      MATL_ID(1,1:2)            = 'GENERIC VEGETATION','MOISTURE'\n")
    fds.write("      MATL_MASS_FRACTION(1,1:2) = 0.937,0.063\n")
    fds.write("      THICKNESS                 = 0.0002\n")
    fds.write("      LENGTH                    = 0.21\n")
    fds.write("      HEAT_TRANSFER_COEFFICIENT = 30.\n")
    fds.write("      GEOMETRY                  = 'CYLINDRICAL' /\n\n")

    fds.write("&SURF ID                        = 'needles' \n")
    fds.write("      MATL_ID(1,1:2)            = 'GENERIC VEGETATION','MOISTURE'\n")
    fds.write("      MATL_MASS_FRACTION(1,1:2) = 0.95,0.05\n")
    fds.write("      THICKNESS                 = 0.02\n")
    fds.write("      LENGTH                    = 0.21\n")
    fds.write("      HEAT_TRANSFER_COEFFICIENT = 30.\n")
    fds.write("      GEOMETRY                  = 'CYLINDRICAL' /\n\n")

    fds.write("&MATL ID = 'GENERIC VEGETATION' \n")
    fds.write("      DENSITY = 500.\n")
    fds.write("      CONDUCTIVITY = 0.1\n")
    fds.write("      SPECIFIC_HEAT= 1.5\n")
    fds.write("      REFERENCE_TEMPERATURE = 200\n")
    fds.write("      PYROLYSIS_RANGE = 30.\n")
    fds.write("      NU_MATL = 0.2\n")
    fds.write("      NU_SPEC = 0.8 \n")
    fds.write("      SPEC_ID = 'CELLULOSE'\n")
    fds.write("      HEAT_OF_COMBUSTION = 15600.\n")
    fds.write("      HEAT_OF_REACTION = 418.\n")
    fds.write("      MATL_ID  = 'CHAR' /\n\n")

    fds.write("&MATL ID = 'MOISTURE' \n")
    fds.write("      DENSITY = 1000.\n")
    fds.write("      CONDUCTIVITY = 0.1\n")
    fds.write("      SPECIFIC_HEAT= 4.184\n")
    fds.write("      REFERENCE_TEMPERATURE = 100.\n")
    fds.write("      PYROLYSIS_RANGE = 10.\n")
    fds.write("      NU_SPEC = 1.0 \n")
    fds.write("      SPEC_ID = 'WATER VAPOR'\n")
    fds.write("      HEAT_OF_REACTION = 2500./\n\n")

    fds.write("&MATL ID = 'CHAR'\n")
    fds.write("      DENSITY  = 100.\n")
    fds.write("      CONDUCTIVITY = 0.1 \n")
    fds.write("      SPECIFIC_HEAT = 1.0 / \n\n")

    fds.write("&MATL ID='DIRT'\n")
    fds.write("      CONDUCTIVITY = 0.25\n")
    fds.write("      SPECIFIC_HEAT = 2.\n")
    fds.write("     DENSITY = 1300. /\n\n")

    fds.write("&PART ID='foliage', DRAG_COEFFICIENT=1.0, SURF_ID='needles', SAMPLING_FACTOR=5,\n")
    fds.write("      QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE DIAMETER', STATIC=.TRUE., COLOR='GREEN' / \n\n")

    fds.write("&PART ID='grass', DRAG_COEFFICIENT=1.0, SURF_ID='grass', SAMPLING_FACTOR=958,\n")
    fds.write("      QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE DIAMETER', STATIC=.TRUE., COLOR='BROWN' /\n\n")

    fds.write("&SURF ID = 'surf1', RGB = 122,117,48, MATL_ID='DIRT', THICKNESS=0.2, PART_ID='grass', PARTICLE_SURFACE_DENSITY=1.0 / \n")
    fds.write("&SURF ID = 'surf2', RGB = 0,100,0, MATL_ID='DIRT', THICKNESS=0.2 / \n\n")
    
    ###################################################################################################################################
    # Writing the obstacles
                                    # Obstacles with no fire
    for ind in Mst.index:

        fds.write(f"&OBST XB={Mst['x'][ind]},{Mst['x'][ind]+Ro},{Mst['y'][ind]},{Mst['y'][ind]+Ro},{Min_z},{Mst['z'][ind]} SURF_ID='surf1' /\n")        
    
########################################################################################################################################
    
    
    fds.close()
    
###############################################################################################################

## Bash/system/OS interaction.

import sys
import os
import subprocess
from subprocess import Popen

def bash(argv):
    arg_seq = [str(arg) for arg in argv]
    #print(arg_seq)
    proc = Popen(arg_seq)#, shell=True)
    proc.wait() #... unless intentionally asynchronous

###############################################################################################################

def reading_hrr(Child, Number_of_meshes):
    filename_txt           = f"fds2ascii.txt"
    fds2ascii_filename = f"{PATH}/FDSFiles/{foldername}/{filename_txt}"
    f2a          = open(fds2ascii_filename, 'w')

    f2a.write(f"{Child} \n")
    f2a.write(f"1\n")
    f2a.write(f"1\n")
    f2a.write(f"n\n")
    for i in range(1,Number_of_meshes+1):
        f2a.write(f"{i}\n")
        f2a.write(f"{Child}_{i}.csv\n")
    f2a.write(f"0\n")
    f2a.close()
    os.chdir(PATH)
    os.chdir(FDS_FOLDER)
    os.system(f"{fds2ascii} < {filename_txt}")
    
##########################################################################
    
def remove_leading_space(file_name):
    # Open the file in read only mode
    Temp_file     = open(f'{file_name[0:-4]}_1.tmp', 'w')
    
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if '.q' in line:
                Temp_file.write(line.lstrip())
            else:
                Temp_file.write(line)
    
    Temp_file.close()
    os.system(f"rm {file_name}")
    os.system(f"mv {file_name[0:-4]}_1.tmp {file_name}")
    return 0    

##########################################################################

def create_job_script_lsf(Child, num_nodes, max_time, omp_threads):
    
    # Create the job submission file for specific region
    job_filename = f"job_{Child}.bsub"
    job_script = open(f"{PATH}/FDSFiles/{foldername}/{job_filename}", 'w')
    
    # Write the contents of the file
    job_script.write("#!/bin/bash\n\n")
    job_script.write(f"#BSUB -n {num_nodes}\n") # Number of compute nodes
    job_script.write(f"#BSUB -J {jobName}\n") # Job Name
    
    output_path = f'{PATH}/FDSFiles/{foldername}/{jobName}_%J'
    job_script.write(f"#BSUB -o {output_path}.out\n")  # Job output file
    job_script.write(f"#BSUB -e {output_path}.err\n")  # Job error file
    
    job_script.write(f"#BSUB -W {max_time}\n\n")       # Maximum time to run on compute node(s)
    
    job_script.write(f"export OMP_NUM_THREADS={omp_threads}\n")                 # Number of OpenMP threads per process
    job_script.write(f"mpiexec -n {number_of_process} {fds_bin} {filename}\n")  # Executes fds on input FDS file
    
    return 0

##########################################################################

def create_job_script_slurm(Child, num_nodes, max_time, omp_threads):
    # Create the job submission file for specific region
    job_filename = f"job_{Child}.sh"
    job_script = open(f"{PATH}/FDSFiles/{foldername}/{job_filename}", 'w')
    
    # Write the contents of the file
    job_script.write("#!/bin/bash\n\n")
    job_script.write(f"#SBATCH --job-name={jobName}\n")         # Job Name 
    
    output_path = f'{PATH}/FDSFiles/{foldername}/{jobName}_%j'
    job_script.write(f"#SBATCH --output={output_path}.out\n")   # Job output file
    job_script.write(f"#SBATCH --error={output_path}.err\n")    # Job error file
    
    job_script.write(f"#SBATCH --nodes={num_nodes}\n")          # Number of compute nodes
    job_script.write(f"#SBATCH --ntasks={number_of_process}")   # Number of MPI processes
    job_script.write(f"#SBATCH --time={max_time}\n\n")          # Max time to run on compute node(s) - (d-hh:mm:ss)
    
    #SBATCH --partition={partition}                             # Specified partition on TACC's Stampede2
    
    job_script.write(f"#SBATCH --mail-user={email}")
    job_script.write(f"#SBATCH --mail-type=all")
    
    job_script.write(f"export OMP_NUM_THREADS={omp_threads}\n") # Number of OpenMP threads per process
    job_script.write(f"ibrun {fds_bin} {filename}\n")           # Executes fds on input FDS file
    
    return 0
    
##########################################################################

def wait_on_lsf():
    monitor = LSFMonitor(USER, jobs) 
    monitor.wait_on_job(jobs[0])  # Waits for the job specified by the user to finish to run the rest of the notebook
    return 0

##########################################################################

def wait_on_slurm():
    monitor = SlurmMonitor(USER, jobs)
    monitor.wait_on_job(jobs[0])  # Waits for the job specified by the user to finish to run the rest of the notebook
    return 0

#############################################################################

def Get_job_id(argv):
    arg_seq = [str(arg) for arg in argv]
    outfile = open('temp.csv', 'w');
    proc = Popen(arg_seq, bufsize=0, stdout=outfile)
    outfile.close()
    proc.wait() #... unless intentionally 
    
    # Using readlines() 
    file1 = open('temp.csv', 'r') 
    Lines = file1.readlines() 
    job_id = Lines[1].split()[0]
    return job_id
###############################################################################
def return_elevation(Mst, x, y):
    elevation = Mst[(Mst['x']==x) & (Mst['y']==y)]['Elevation']
    if (len(elevation) != 0):
       elevation = int(elevation)
       return elevation
    else:
       return Mst.min()['Elevation']
    

def delete_under(Hrr):
    
    for ind in Hrr.index:
        x = Hrr['x'][ind]
        y = Hrr['y'][ind] 
        elevation = return_elevation(Mst, x, y)
        diferencia = elevation - Hrr['z'][ind]
        if (diferencia>0):
            Hrr = Hrr.drop([ind])
      
    return Hrr

########################################################################################

def draw_rectangle(image_in,width,height,xlb,xub,ylb,yub,image_out,color):
    # Drawing a rectangle in a picture
    dpi = 80
                  
    im  = Image.open(image_in)
    ratiox = im.size[0]/width
    ratioy = im.size[1]/height
    
    xlb = xlb*ratiox
    xub = xub*ratiox
    
    ylb = ylb*ratioy
    yub = yub*ratioy
    
    # What size does the figure need to be in inches to fit the image?
    figsize = width / float(dpi), height / float(dpi)
    
    figure = plt.figure(figsize=figsize)
    ax = figure.add_axes([0, 0, 1, 1])
    # Hide spines, ticks, etc.
    ax.axis('off')
    rect = matplotlib.patches.Rectangle((xlb,im.size[1]-yub),xub-xlb,yub-ylb, edgecolor=color, facecolor="none")   
    ax.imshow(im)
    ax.add_patch(rect)
    figure.savefig(image_out,dpi=dpi,transparent=True)
    return 0

def crop_rectangle(image_in,width,height,xlb,xub,ylb,yub,image_out):
    # Cropping a rectangle from a picture
    im  = Image.open(image_in)
    ratiox = im.size[0]/width
    ratioy = im.size[1]/height
    
    xlb = xlb*ratiox
    xub = xub*ratiox
    
    ylb = ylb*ratioy
    yub = yub*ratioy
    
    
    box = (xlb,im.size[1]-yub,xub,im.size[1]-ylb)
    im.crop(box).save(image_out)
    return 0

######################################################################################################################################

def setting_devices(elevation_file,resolution,quantity,buffer,border,output_file):
    # Reading the elevation file
    elevation = pd.read_csv(elevation_file)
    
    # Extracting a uniformlly sample of the elevation of a given resolution
    elevation = elevation[(elevation.x%resolution==0) & (elevation.y%resolution==0)]  # Filters data 
    
    device     = open(output_file, 'w')
   
    for i in range(0,elevation.shape[0]):
        if(elevation.iloc[i]['x']> border[0] and elevation.iloc[i]['x']< border[1] and elevation.iloc[i]['y'] > border[2] and elevation.iloc[i]['y'] < border[3]):
            device.write(f"&DEVC ID='DEV_%03d{quantity[0]}', XYZ={elevation.iloc[i]['x']+buffer},{elevation.iloc[i]['y']+buffer},{math.ceil(elevation.iloc[i]['z'])+buffer},IOR=3, QUANTITY='{quantity}' \n" %(i))
    device.close()
    return elevation

############################################################################################################################################

def setting_initialization(hrrpuv_df,resolution,output_file):
    
    initialization     = open(output_file, 'w')
        
    for ind in hrrpuv_df.index:
        initialization.write(f"&INIT XB={hrrpuv_df['x'][ind]-resolution},{hrrpuv_df['x'][ind]},{hrrpuv_df['y'][ind]-resolution},{hrrpuv_df['y'][ind]},{hrrpuv_df['z'][ind]-resolution},{hrrpuv_df['z'][ind]}, HRRPUV={hrrpuv_df['hrr'][ind]}, RAMP_Q='fire' /  \n")
    initialization.close()
    return hrrpuv_df

############################################################################################################################################

def reading_devices(elevation_file,resolution,sufix,border):
    # Reading the elevation file
    elevation = pd.read_csv(elevation_file)
    
    # Extracting a uniformlly sample of the elevation of a given resolution
    elevation = elevation[(elevation.x%resolution==0) & (elevation.y%resolution==0)]  # Filters data 
    
    device_names     = []
    
    for i in range(0,elevation.shape[0]):
        if(elevation.iloc[i]['x']> border[0] and elevation.iloc[i]['x']< border[1] and elevation.iloc[i]['y'] > border[2] and elevation.iloc[i]['y'] < border[3]):
            device_names.append(f"DEV_%03d{sufix}" %(i))
            
    return device_names

def reading_slide(child,quantity,first,step,meshes,path,t_start,t_end,file):
    output_file = path+file
    column_names = ["x", "y", "z", "hrr"]
    hrrpuv = pd.DataFrame(columns = column_names)
    for i in range(meshes):
        fds     = open(output_file, 'w')
        fds.write(f"{child}\n")
        fds.write(f"2\n")
        fds.write(f"1\n")
        fds.write(f"n\n")
        fds.write(f"{t_start} {t_end}\n")
        fds.write(f"1\n")
        fds.write(f"{first}\n")
        first = first + step
        fds.write(f"{quantity}_{i+1}.csv\n")
        fds.close()
        os.chdir(path)
        os.system(f"fds2ascii < {file}")
        temp = pd.read_csv(f"{quantity}_{i+1}.csv",skiprows = 2, header=None)
        temp.columns=['x','y','z','hrr']
        hrrpuv = pd.concat([hrrpuv,temp]) 
    return hrrpuv

def Elevation(file,searchExp):
    with open(file, 'r', encoding='utf8') as dsvfile:
        lines = dsvfile.readlines()
        lines = [line.rstrip('\n') for line in lines]
        elevation = []
        for line in lines:
            if searchExp in line:
                split_line = line.split(',')
                x = split_line[0].split('=')
                x = float(x[1])
                
                y = float(split_line[2])
                
                z = split_line[5].split(' ')
                z = float(z[0])
                elevation.append([x,y,z])
        return elevation
    

def devices_output(devices_files,devices_fds,threshold,region,output):
    # Reading the location of the devices 
    #scaler = MinMaxScaler()
    device_start = 1
    device_end   = 0;
    thr_index    = 0;
    for files in devices_files:

        with open(files, 'r', encoding='utf8') as dsvfile:
            lines = dsvfile.readlines()
            lines = [line.rstrip('\n') for line in lines]
            devices_coordinates = []
            for line in lines:
                    split_line = line.split(',')
                    x = split_line[1].split('=')[1]
                    y = split_line[2]
                    devices_coordinates.append([float(x),float(y)])
            # Reading the device quantity
            #quantity = str(split_line[5].split('=')[1])[1:-1]
            quantity = files.split('.')
            quantity = quantity[-2]
            quantity = quantity.split('_')
            quantity = str(quantity[-1])
            
            devices_coordinates = np.array(devices_coordinates)

            devices_df = pd.read_csv(devices_fds,skiprows = 1)
            number_of_devices = devices_coordinates.shape[0] 
            device_end        = device_end + number_of_devices
            Temp1 = devices_df[devices_df.columns[device_start:device_end+1]].values
            device_start = device_end+1
            Temp1 = np.transpose(Temp1)
            
            maximo = Temp1.max() 
            
            Temp1[Temp1 < threshold[thr_index]*maximo ] = 0
            thr_index = thr_index + 1
            
            devices = np.concatenate((devices_coordinates,Temp1), axis=1)
            
            devices = pd.DataFrame(devices)
            time = devices.shape[1]
            isdir = os.path.isdir(f'{output}/{region}/{quantity}')

            if not isdir:
                os.makedirs(f'{output}/{region}/{quantity}')

            for i in range(2,time):
                soil_map(devices, out=f'{output}/{region}/{quantity}/{quantity}%04d.png' %(i-2), size=3.0,title=f'{quantity}',cmap=plt.cm.get_cmap('RdPu'),value=devices[devices.columns[i]], vmax = 1600)
    return devices
    


######################################################################################################################

def soil_map(df, title="Soil Moisture Heatmap", out="", cmap=cmap_rg, legend="Soil Moisture", size=.05, vmin=None, vmax=None, value=2):
    
    if df.shape[1]<3:
        raise ValueError("The dataframe doesn't have enough columns.")
    elif df.shape[1]>3:
        #print("The dataframe has too many columns, so we're dropping all but the first three.")
        df = df[df.columns[:3]]
    heatmap(df, title=title, out=out, cmap=cmap, size=size, vmin=vmin, vmax=vmax, value=value)
    

# General heatmap function. 
def heatmap(df, horizontal=0, vertical=1, value=2, vmin=None, vmax=None, size=1, title="Heatmap", out="", cmap=None):
    df.plot.scatter(x=horizontal, y=vertical, s=size, c=value, cmap=cmap, title=title, vmin=vmin, vmax=vmax)
    if out:
        #print(f"Saving image to {out}")
        plt.savefig(out, dpi=200)
        #plt.show()
    else:
        plt.show()
    plt.close()
    
#########################################################################################################################################
def tail(filename, n=10):
    'Return the last n lines of a file'
    with open(filename) as f:
        return deque(f, n)