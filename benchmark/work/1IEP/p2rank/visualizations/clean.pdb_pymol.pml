from pymol import cmd,stored

set depth_cue, 1
set fog_start, 0.4

set_color b_col, [36,36,85]
set_color t_col, [10,10,10]
set bg_rgb_bottom, b_col
set bg_rgb_top, t_col      
set bg_gradient

set  spec_power  =  200
set  spec_refl   =  0

load "data/clean.pdb", protein
create ligands, protein and organic
select xlig, protein and organic
delete xlig

hide everything, all

color white, elem c
color bluewhite, protein
#show_as cartoon, protein
show surface, protein
#set transparency, 0.15

show sticks, ligands
set stick_color, magenta




# SAS points

load "data/clean.pdb_points.pdb.gz", points
hide nonbonded, points
show nb_spheres, points
set sphere_scale, 0.2, points
cmd.spectrum("b", "green_red", selection="points", minimum=0, maximum=0.7)


stored.list=[]
cmd.iterate("(resn STP)","stored.list.append(resi)")    # read info about residues STP
lastSTP=stored.list[-1] # get the index of the last residue
hide lines, resn STP

cmd.select("rest", "resn STP and resi 0")

for my_index in range(1,int(lastSTP)+1): cmd.select("pocket"+str(my_index), "resn STP and resi "+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.show("spheres","pocket"+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.set("sphere_scale","0.4","pocket"+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.set("sphere_transparency","0.1","pocket"+str(my_index))



set_color pcol1 = [0.361,0.576,0.902]
select surf_pocket1, protein and id [2500,2501,2502,3053,3056,3454,3052,2472,2491,3063,3087,3042,2498,2499,2496,2497,2523,2468,2469,3022,3024,2470,3020,3023,3025,3028,3036,2522,2471,2875,3003,3008,3015,3030,2632,3004,2640,2644,2646,2985,3545,3547,3548,2874,3534,3453,2775,3533,3539,3542,2648,2630,2631,2799,2800,2988] 
set surface_color,  pcol1, surf_pocket1 
set_color pcol2 = [0.302,0.278,0.702]
select surf_pocket2, protein and id [204,231,233,235,236,1279,1281,230,256,257,1275,202,205,206,225,234,737,1263,532,533,608,738,1267,509,378,380,381,382,366,754,374,203,756,759,1187,1189,742,762,758,790,777,786,787,1188,1264,1268,797,793] 
set surface_color,  pcol2, surf_pocket2 
set_color pcol3 = [0.631,0.361,0.902]
select surf_pocket3, protein and id [532,533,608,619,1267,509,506,531,558,560,530,524,525,526,599,556,606,1255,1055,1098,602,1260,1261,1262,1264,1117,1268,1271,1111,1113,1105] 
set surface_color,  pcol3, surf_pocket3 
set_color pcol4 = [0.678,0.278,0.702]
select surf_pocket4, protein and id [2798,2800,2824,2826,2872,2772,3377,3379,3371,3321,3320,2868,2790,2791,2792,3361,3364,3526,3527,3530,2874,3534,3521,2775,3533,3383,3535,3537] 
set surface_color,  pcol4, surf_pocket4 
set_color pcol5 = [0.902,0.361,0.682]
select surf_pocket5, protein and id [381,382,467,479,508,474,445,446,447,442,443,466,468,473,396,229,1319,239,242,1275,386,405,406,1305,1286,1284,469] 
set surface_color,  pcol5, surf_pocket5 
set_color pcol6 = [0.702,0.278,0.341]
select surf_pocket6, protein and id [1683,1679,1932,1943,1643,1942,1967,1968,2183,1680,1682,1930,921,941,945,946,949,951,919,922,1677,943,977] 
set surface_color,  pcol6, surf_pocket6 
set_color pcol7 = [0.902,0.522,0.361]
select surf_pocket7, protein and id [3207,3205,3206,3211,3212,3187,3209,3185,3188,3945,3943,3946,3913,4449,3243,3215,3217,4208,4233,4234,3909,4196,4209,3949] 
set surface_color,  pcol7, surf_pocket7 
set_color pcol8 = [0.702,0.596,0.278]
select surf_pocket8, protein and id [3986,3723,3724,3079,3116,3429,3431,3078,3935,3618,3593,3985,3993] 
set surface_color,  pcol8, surf_pocket8 
   

deselect

orient
