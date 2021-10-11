# MelodyGen v3 - Level Generator for Angry Birds Using Auto-Generated Melodies

This program is an algorithmic game level generator that uses using music theory to create Angry Birds levels. 

Different iterations of this project was awarded the following prizes:

**IEEE Conference on Games, Osaka, Japan (Aug 2020)**\
>*Angry Birds Artificial Intelligence Competition, 1st Prize recipient in Procedural Level Generation Category*
  
**IEEE Conference on Games, London, UK (Aug 2019)**\
>*Angry Birds Artificial Intelligence Competition, 1st Prize recipient in Procedural Level Generation Category*
  
**IEEE Conference on CIG, Maastricht, The Netherlands (Aug 2018)**\
>*Angry Birds Artificial Intelligence Competition, 2nd Prize recipient in Procedural Level Generation Category*


## Overview

This project was written using python3.8 interpreter. If you have an older version, you may need to update your version.

The outputs of the program are: xml and MIDI files. xml files contain the level data and should be carried to the following path to be loaded to the game: ⁨
Science-Birds-OSX⁩ ▸ ⁨Science-Birds-OSX.app⁩ ▸ ⁨Contents⁩ ▸ ⁨Resources⁩ ▸ ⁨Data⁩ ▸ ⁨StreamingAssets⁩ ▸ Levels. The first 3 levels 
are built in, generated levels start from level 4. The MIDI files are the generative melodies of the corresponding 
levels. These can be used for listening to and displaying the melodies.

## Dependencies

This level generator uses two packages that needs to be installed: pygame and music21
Directions for installing these packages, check out the links below:

WARNING: "pip install pygame" command causes issues on MacOS machines, use "python3 -m pip install -U pygame==2.0.0.dev6 --user" instead. 
Also, pygame causes issues when used with a virtual environment in MacOS. For more information and a potential solution, see the link below.

music21:
http://web.mit.edu/music21/doc/usersGuide/usersGuide_01_installing.html

pygame:
https://www.pygame.org/wiki/GettingStarted


