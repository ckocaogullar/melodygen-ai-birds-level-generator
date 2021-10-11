
from random import randint
from random import uniform
from random import choice
from math import sqrt, ceil, floor
from copy import deepcopy
from music21 import *
from music21 import chord
from music21 import stream
from music21 import converter
import itertools
import pygame
from _threading_local import local

# AIBirds Procedural Level Generation Competition 2020
# Procedural Level Generation Using Auto-Generated Melodies
# Ceren Kocaogullar, University of Cambridge, UK

# See README.txt for installation and other details

# blocks number and size
blocks = {'1': [0.84, 0.84], '2': [0.85, 0.43], '3': [0.43, 0.85], '4': [0.43, 0.43],
          '5': [0.22, 0.22], '6': [0.43, 0.22], '7': [0.22, 0.43], '8': [0.85, 0.22],
          '9': [0.22, 0.85], '10': [1.68, 0.22], '11': [0.22, 1.68],
          '12': [2.06, 0.22], '13': [0.22, 2.06]}

# blocks number and name
# (blocks 3, 7, 9, 11 and 13) are their respective block names rotated 90 derees clockwise
block_names = {'1': "SquareHole", '2': "RectFat", '3': "RectFat", '4': "SquareSmall",
               '5': "SquareTiny", '6': "RectTiny", '7': "RectTiny", '8': "RectSmall",
               '9': "RectSmall", '10': "RectMedium", '11': "RectMedium",
               '12': "RectBig", '13': "RectBig"}

# additional objects number and name
additional_objects = {'1': "TriangleHole",
                      '2': "Triangle", '3': "Circle", '4': "CircleSmall"}

# additional objects number and size
additional_object_sizes = {'1': [0.82, 0.82], '2': [
    0.82, 0.82], '3': [0.8, 0.8], '4': [0.45, 0.45]}

# blocks number and probability of being selected
probability_table_blocks = {'1': 0.10, '2': 0.10, '3': 0.10, '4': 0.05,
                            '5': 0.02, '6': 0.05, '7': 0.05, '8': 0.10,
                            '9': 0.05, '10': 0.16, '11': 0.04,
                            '12': 0.16, '13': 0.02}

# materials that are available
materials = ["wood", "stone", "ice"]

# bird types number and name
bird_names = {'1': "BirdRed", '2': "BirdBlue",
              '3': "BirdYellow", '4': "BirdBlack", '5': "BirdWhite"}

# bird types number and probability of being selected
bird_probabilities = {'1': 0.35, '2': 0.2, '3': 0.2, '4': 0.15, '5': 0.1}

TNT_block_probability = 0.3

pig_size = [0.5, 0.5]  # size of pigs

platform_size = [0.62, 0.62]  # size of platform sections

# buffer uesd to push edge blocks further into the structure center (increases stability)
edge_buffer = 0.11

absolute_ground = -3.5  # the position of ground within level

max_peaks = 5  # maximum number of peaks a structure can have (up to 5)
min_peak_split = 10  # minimum distance between two peak blocks of structure
max_peak_split = 50  # maximum distance between two peak blocks of structure

minimum_height_gap = 3.5  # y distance min between platforms
# x_distance min between platforms / y_distance min between platforms and ground structures
platform_distance_buffer = 0.4

# defines the levels area (ie. space within which structures/platforms can be placed)
level_width_min = -3.0
level_width_max = 9.0
# only used by platforms, ground structures use absolute_ground to determine their lowest point
level_height_min = -2.0
level_height_max = 6.0

pig_precision = 0.01  # how precise to check for possible pig positions on ground

min_ground_width = 2.07  # minimum amount of space allocated to ground structure
# desired height limit of ground structures
ground_structure_height_limit = (
    (level_height_max - minimum_height_gap) - absolute_ground) / 1.5

max_attempts = 100  # number of times to attempt to place a platform before abandoning it

# AIBirds Level Generation With Songs, Using Melodies

################################################## NEW VERSION ############################################################

# a list of notes from c to b in a c major scale, 'r' for rests, multiple 'r's added to the array to increase the chance of them being selected
notes = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'b-', 'b']
# array for keeping track of the used notes for creating atonal melodies
used_notes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# array for keeping track of which notes are in tone, for creating tonal melodies
intone_notes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
root_note = -1  # variable that keeps the root note determining the tone

# flags and variables used for determining the musical nature of the level


####### PLEASE ADJUST THESE PARAMETERS HOWEVER YOU WANT THE ALGORITHM TO BEHAVE ######

# flags for tonal property of the melody only one of these flags should be True.
is_major = False
is_minor = False
is_atonal = True

# variables for determining the probability percentage of double note structures and rests.
# NOTE: Note that only usable percentages for rests are %0, %25, %50 and %75
double_prob_percentage = 100
rest_percentage = 25

###### END OF ADJUSTABLE PARAMETERS ####

freq_inits = []
durat_inits = []
freqs = []
durats = []
platform_indexes = []
total_ground_pos = []
lvl_cnt = 0
durat_cnt = 0
platform_cnt = 0
num_platforms = 0


class ChordState(tinyNotation.State):

    def affectTokenAfterParse(self, n):
        super(ChordState, self).affectTokenAfterParse(n)
        return None  # do not append Note object

    def end(self):
        ch = chord.Chord(self.affectedTokens)
        ch.duration = self.affectedTokens[0].duration
        return ch


def generate_stream(number_levels):
    global used_notes
    global root_note
    is_tonal = False
    local_durats = []
    local_freqs = []
    string = "4/4 "
    tracker = 0.0
    curdur = 4
    tnc = tinyNotation.Converter()
    tnc.bracketStateMapping['chord'] = ChordState

    if(is_minor or is_major):
        is_tonal = True
    ################################################################################
    while(tracker < 1):
        # determine whether a note or a double note structure
        cn = randint(1, 100)
        # a note (not a double note structure) with the probability determined by the user above
        if(cn <= 100 - double_prob_percentage):
            # pick a random note or rest
            i = randint(0, len(notes) - 1)

            ################################################################################
            # The following while loop is for creating "atonal" melodies
            # find an unused note
            if(is_atonal):
                # while(used_notes[i] != 0):
                #     i = randint(0, len(notes) - 1)
                # string += notes[i]
                # used_notes[i] = 1  # tag the note as used

                unused_note_indexes = []
                for i in range(11):
                    if used_notes[i] == 0:
                        unused_note_indexes.append(i)
                if len(unused_note_indexes) == 0:
                    used_notes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                ind = choice(unused_note_indexes)
                string += notes[ind]
                
                used_notes[ind] = 1  # tag the note as used
                unused_note_indexes.remove(ind)
                print(f'used notes {used_notes}')
                print(f'string {string}')
            ################################################################################

            ################################################################################
            # The following while loop is for creating "tonal" melodies (either major or minor in this case
            # find an unused note
            if(is_tonal):

                ################################################################################
                # The following section is for creating melodies in tone.
                # Picking the root note of the scale, the first selected note becomes this root note
                if(root_note == -1):
                    i = randint(0, 11)
                    root_note = i
                    # Minor scale
                    if(is_minor):
                        intone_notes[i] = 1
                        intone_notes[(i + 2) % 12] = 1
                        intone_notes[(i + 3) % 12] = 1
                        intone_notes[(i + 5) % 12] = 1
                        intone_notes[(i + 7) % 12] = 1
                        intone_notes[(i + 8) % 12] = 1
                        intone_notes[(i + 10) % 12] = 1

                    # Major scale
                    elif(is_major):
                        intone_notes[i] = 1
                        intone_notes[(i + 2) % 12] = 1
                        intone_notes[(i + 4) % 12] = 1
                        intone_notes[(i + 5) % 12] = 1
                        intone_notes[(i + 7) % 12] = 1
                        intone_notes[(i + 9) % 12] = 1
                        intone_notes[(i + 11) % 12] = 1

                while(intone_notes[i] != 1):
                    i = randint(0, len(notes) - 1)

                string += notes[i]
            ################################################################################

            # add the note's relative frequency (with respect to C) to the local frequency array
            local_freqs.append(i + 1)
            # if(octa >= 7):

            # determine the durationn
            # making sure that we write a melody that is exactly one bar:

            d = randint(0, 10)
            if(1 - tracker == 0.125):
                if(d <= 5):
                    if(curdur != 8):
                        string += '8'
                        curdur = 8
                else:
                    if(curdur != 16):
                        string += '16'
                        curdur = 16
            elif(1 - tracker == 0.0625):
                if(curdur != 16):
                    string += '16'
                    curdur = 16
            elif(d <= 4):
                if(curdur != 4):
                    string += '4'
                    curdur = 4
            elif(d > 4):
                if(d <= 7):
                    if(curdur != 8):
                        string += '8'
                        curdur = 8
            elif(d > 7):
                if(curdur != 16):
                    string += '16'
                    curdur = 16

            string += " "
        # a chord with the remaining probability
        else:
            string += "chord{"
            # pick two notes, add a duration symbol to the first one
            i = randint(0, 11)  # the first note

            ################################################################################
            # The following while loop is for creating "atonal" melodies
            # find an unused note
            if(is_atonal):
                # while(used_notes[i] != 0):
                #     i = randint(0, 11)
                # string += notes[i]
                # used_notes[i] = 1  # tag the note as used
                # print(f'used notes {used_notes}')

                unused_note_indexes = []
                for i in range(11):
                    if used_notes[i] == 0:
                        unused_note_indexes.append(i)
                if len(unused_note_indexes) == 0:
                    used_notes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                ind = choice(unused_note_indexes)
                string += notes[ind]

                used_notes[ind] = 1  # tag the note as used
                unused_note_indexes.remove(ind)
                print(f'unused_note_indexes {unused_note_indexes}')
                print(f'used notes {used_notes}')
                print(f'string {string}')
            ################################################################################

            ################################################################################
            # The following while loop is for creating "tonal" melodies (either major or minor in this case
            # find an unused note

            if(is_tonal):

                ################################################################################
                # The following section is for creating melodies in tone.
                # Picking the root note of the scale, the first selected note becomes this root note

                if(root_note == -1):
                    i = randint(0, 11)
                    root_note = i
                    # Minor scale
                    if(is_minor):
                        intone_notes[i] = 1
                        intone_notes[(i + 2) % 12] = 1
                        intone_notes[(i + 3) % 12] = 1
                        intone_notes[(i + 5) % 12] = 1
                        intone_notes[(i + 7) % 12] = 1
                        intone_notes[(i + 8) % 12] = 1
                        intone_notes[(i + 10) % 12] = 1

                    # Major scale
                    elif(is_major):
                        intone_notes[i] = 1
                        intone_notes[(i + 2) % 12] = 1
                        intone_notes[(i + 4) % 12] = 1
                        intone_notes[(i + 5) % 12] = 1
                        intone_notes[(i + 7) % 12] = 1
                        intone_notes[(i + 9) % 12] = 1
                        intone_notes[(i + 11) % 12] = 1

                while(intone_notes[i] != 1):
                    i = randint(0, 11)

                string += notes[i]
            ################################################################################

            string += notes[i]

            # determine the duration
            d = randint(0, 10)
            if(1 - tracker == 0.125):
                if(d <= 5):
                    if(curdur != 8):
                        string += '8'
                        curdur = 8
                else:
                    if(curdur != 16):
                        string += '16'
                        curdur = 16
            elif(1 - tracker == 0.0625):
                if(curdur != 16):
                    string += '16'
                    curdur = 16
            elif(d <= 4):
                if(curdur != 4):
                    string += '4'
                    curdur = 4
            elif(d > 4):
                if(d <= 7):
                    if(curdur != 8):
                        string += '8'
                        curdur = 8
            elif(d > 7):
                if(curdur != 16):
                    string += '16'
                    curdur = 16
            string += " "
            ttl = 0  # time to leave: a counter for trying to find a musically contenting second note for a limited amount of time
            j = randint(0, 11)  # the second note

            ################################################################################
            # The following while loop is for creating "atonal" melodies
            # find an unused note

            if(is_atonal):
                while(used_notes[j] != 0):
                    j = randint(0, 11)
                string += notes[j]
                used_notes[j] = 1  # tag the note as used

            ################################################################################

            ################################################################################
            # The following while loop is for creating "tonal" melodies (either major or minor)
            if(is_tonal):

                ################################################################################
                # The following section is for creating melodies in tone.
                # Picking the root note of the scale, the first selected note becomes this root note
                if(root_note == -1):
                    # WARNING PROBLEM TODO: picks the rest as root as well, seems to pick the root only once, not for every level
                    j = randint(0, 11)
                    root_note = j
                    # Minor scale
                    if(is_minor):
                        intone_notes[j] = 1
                        intone_notes[(j + 2) % 12] = 1
                        intone_notes[(j + 3) % 12] = 1
                        intone_notes[(j + 5) % 12] = 1
                        intone_notes[(j + 7) % 12] = 1
                        intone_notes[(j + 8) % 12] = 1
                        intone_notes[(j + 10) % 12] = 1

                    # Major scale
                    elif(is_major):
                        intone_notes[j] = 1
                        intone_notes[(j + 2) % 12] = 1
                        intone_notes[(j + 4) % 12] = 1
                        intone_notes[(j + 5) % 12] = 1
                        intone_notes[(j + 7) % 12] = 1
                        intone_notes[(j + 9) % 12] = 1
                        intone_notes[(j + 11) % 12] = 1

                while(intone_notes[j] != 1):
                    j = randint(0, 11)

                string += notes[j]
            ################################################################################

            while (abs(i - j) == 1 or abs(i - j) == 2 or ttl >= 40):
                j = randint(0, 11)  # the second note
                ttl += 1
            if(ttl >= 40):  # if no musically contenting second note was found in the limited steps, make the second note the same as the first one
                j = i
            string += notes[j]
            string += "} "
            # add the chord as a list to the local frequency list
            local_freqs.append([i + 1, j + 1])
        local_durats.append(float(1.0 / float(curdur)))
        tracker += float(1.0 / float(curdur))

    freq_inits.append(local_freqs)
    durat_inits.append(local_durats)
    normalize_song(number_levels)
    platform_indexes.append([])
    for i in range(len(freqs[number_levels])):
        if isinstance(freqs[number_levels][i], list):
            platform_indexes[-1].append(i)
    tnc.load(string)
    tnc.parse()
    str1 = tnc.stream
    # str1.show()
    str1.write('midi', 'level_music_' + str(number_levels+4) + '.mid')

    pygame.init()

    pygame.mixer.music.load('level_music_' + str(number_levels+4) + '.mid')

    # Uncomment this line to hear the generative melodies as they are created
    # pygame.mixer.music.play()

    for i in range(len(notes)):
        used_notes[i] = 0
        intone_notes[i] = 0

    root_note = - 1

    while pygame.mixer.music.get_busy():
        pygame.time.wait(1000)

###############################################################################################################################

# Following is the helper methods for generating levels using musical attributes of the songs

###############################################################################################################################


# Find the boundary values for frequencies, for later use in normalizing values using the ranges given for the game

def find_freq_ceil(number_level):
    global freq_inits
    messages = deepcopy(freq_inits[number_level])
    ceil_freq = -1
    for i in range(len(messages)):
        if(isinstance(messages[i], list)):
            for j in range(len(messages[i])):
                if(messages[i][j] > ceil_freq):
                    if(messages[i][j] != 0):
                        ceil_freq = messages[i][j]
        else:
            if(messages[i] > ceil_freq):
                ceil_freq = messages[i]

    # handling the case where the song consists of only rests
    if(ceil_freq <= 0):
        return -1
        raise ValueError("ERROR: THE SONG CONSISTS OF RESTS ONLY")
    return ceil_freq


# a method for normalizing a single frequency

def freq_normalizer(fr, number_level):
    ceil_f = find_freq_ceil(number_level)
    if(ceil_f == -1):
        raise ValueError("ERROR: THE SONG CONSISTS OF RESTS ONLY")
    if(fr == 0):  # if it is a rest, the height of the structure will be zero
        return fr
    elif(isinstance(fr, list)):
        for i in range(len(fr)):
            fr[i] = level_height_max * fr[i] / ceil_f
        return fr
    else:  # if it is a note, normalize
        return level_height_max * fr / ceil_f

# a method for normalizing a single duration


def durat_normalizer(dur):
    if(dur < 0):
        raise ValueError("DURATION VALUE %d IS NEGATIVE" % dur)
    return (level_width_max - level_width_min) * float(dur)

# a method for normalizing the whole frequencies and durations of the notes of a melody


def normalize_song(number_level):
    global freqs
    global durats
    global freq_inits
    global durat_inits
    freqs.append([])
    durats.append([])
    for msg in range(len(durat_inits[number_level])):  # then normalize
        # Normalize the frequencies and add them to the freq array in the order they appear in the song
        freqs[-1].append(freq_normalizer(freq_inits[number_level]
                                         [msg], number_level))
        # Normalize the durations and add them to the freq array in the order they appear in the song.
        durats[-1].append(durat_normalizer(durat_inits[number_level][msg]))


# checks if the tonal flags are set correctly

def all_tone_check():
    if((is_major or is_minor or is_atonal) == False):
        raise ValueError(
            "INVALID TONALITY INPUT: A MELODY SHOULD HAVE A TONALITY PROPERTY DETERMINED.")


def tonal_tone_check():
    if(is_major and is_minor):
        raise ValueError(
            "INVALID TONALITY INPUT: A MELODY CANNOT BE MAJOR AND MINOR AT THE SAME TIME")


# checks if the double note probability is a valid value

def double_note_check():
    if(double_prob_percentage < 0 or double_prob_percentage > 100):
        raise ValueError(
            "INVALID DOUBLE NOTE PROBABILITY VALUE. PLEASE ENTER A VALUE BETWEEN 0-100")

# checks if the rest probability is a valid value


def rest_check():
    if(not(rest_percentage == 0 or rest_percentage == 25 or rest_percentage == 50 or rest_percentage == 75)):
        raise ValueError(
            "INVALID REST PERCENTAGE. PLEASE ENTER A VALID PERCENTAGE: EITHER 0 or 25 or 50 or 75")


# adjusts the note, intone_note and used_note lists according to the number of rests determined by the user in variable number of rests

def rest_adjust():
    number_of_rests = 0
    if(rest_percentage >= 0):
        if(rest_percentage == 25):
            number_of_rests = 4
        if(rest_percentage == 50):
            number_of_rests = 12
        if(rest_percentage == 75):
            number_of_rests = 36
        for i in range(number_of_rests):
            notes.append('r')
            used_notes.append(0)
            intone_notes.append(1)

# generates a list of all possible subsets for structure bottom

##########################################################################################################################

# The following part of the program was provided by AIBirds Level Generation Competition and modified by Ceren Kocaogullar.


def generate_subsets(current_tree_bottom):
    current_distances = []
    subsets = []
    current_point = 0
    while current_point < len(current_tree_bottom) - 1:
        current_distances.append(
            current_tree_bottom[current_point + 1][1] - current_tree_bottom[current_point][1])
        current_point = current_point + 1

    # remove similar splits causesd by floating point imprecision
    for i in range(len(current_distances)):
        current_distances[i] = round(current_distances[i], 10)

    # all possible x-distances between bottom blocks
    split_points = list(set(current_distances))

    for i in split_points:  # subsets based on differences between x-distances
        current_subset = []
        start_point = 0
        end_point = 1
        for j in current_distances:
            if j >= i:
                current_subset.append(
                    current_tree_bottom[start_point:end_point])
                start_point = end_point
            end_point = end_point + 1

        current_subset.append(current_tree_bottom[start_point:end_point])

        subsets.append(current_subset)

    subsets.append([current_tree_bottom])

    return subsets

# finds the center positions of the given subset


def find_subset_center(subset):
    if len(subset) % 2 == 1:
        return subset[(len(subset) - 1) // 2][1]
    else:
        return (subset[len(subset) // 2][1] - subset[(len(subset) // 2) - 1][1]) / 2.0 + subset[(len(subset) // 2) - 1][1]

# finds the edge positions of the given subset


def find_subset_edges(subset):
    edge1 = subset[0][1] - (blocks[str(subset[0][0])][0]) / 2.0 + edge_buffer
    edge2 = subset[-1][1] + (blocks[str(subset[-1][0])][0]) / 2.0 - edge_buffer
    return[edge1, edge2]

# checks that positions for new block dont overlap and support the above blocks


def check_valid(grouping, choosen_item, current_tree_bottom, new_positions):

    # check no overlap
    i = 0
    while i < len(new_positions) - 1:
        if (new_positions[i] + (blocks[str(choosen_item)][0]) / 2) > (new_positions[i + 1] - (blocks[str(choosen_item)][0]) / 2):
            return False
        i = i + 1

    # check if each structural bottom block's edges supported by new blocks
    for item in current_tree_bottom:
        edge1 = item[1] - (blocks[str(item[0])][0]) / 2
        edge2 = item[1] + (blocks[str(item[0])][0]) / 2
        edge1_supported = False
        edge2_supported = False
        for new in new_positions:
            if ((new - (blocks[str(choosen_item)][0]) / 2) <= edge1 and (new + (blocks[str(choosen_item)][0]) / 2) >= edge1):
                edge1_supported = True
            if ((new - (blocks[str(choosen_item)][0]) / 2) <= edge2 and (new + (blocks[str(choosen_item)][0]) / 2) >= edge2):
                edge2_supported = True
        if edge1_supported == False or edge2_supported == False:
            return False
    return True

# check if new block can be placed under center of bottom row blocks validly


def check_center(grouping, choosen_item, current_tree_bottom):
    new_positions = []
    for subset in grouping:
        new_positions.append(find_subset_center(subset))
    return check_valid(grouping, choosen_item, current_tree_bottom, new_positions)

# check if new block can be placed under edges of bottom row blocks validly


def check_edge(grouping, choosen_item, current_tree_bottom):
    new_positions = []
    for subset in grouping:
        new_positions.append(find_subset_edges(subset)[0])
        new_positions.append(find_subset_edges(subset)[1])
    return check_valid(grouping, choosen_item, current_tree_bottom, new_positions)

# check if new block can be placed under both center and edges of bottom row blocks validly


def check_both(grouping, choosen_item, current_tree_bottom):
    new_positions = []
    for subset in grouping:
        new_positions.append(find_subset_edges(subset)[0])
        new_positions.append(find_subset_center(subset))
        new_positions.append(find_subset_edges(subset)[1])
    return check_valid(grouping, choosen_item, current_tree_bottom, new_positions)

# choose a random item/block from the blocks dictionary based on probability table


def choose_item(table):
    ran_num = uniform(0.0, 1.0)
    selected_num = 0
    while ran_num > 0:
        selected_num = selected_num + 1
        ran_num = ran_num - table[str(selected_num)]
    return selected_num

# finds the width of the given structure


def find_structure_width(structure):
    min_x = 999999.9
    max_x = -999999.9
    for block in structure:
        if round((block[1] - (blocks[str(block[0])][0] / 2)), 10) < min_x:
            min_x = round((block[1] - (blocks[str(block[0])][0] / 2)), 10)
        if round((block[1] + (blocks[str(block[0])][0] / 2)), 10) > max_x:
            max_x = round((block[1] + (blocks[str(block[0])][0] / 2)), 10)
    return (round(max_x - min_x, 10))

# finds the height of the given structure


def find_structure_height(structure):
    min_y = 999999.9
    max_y = -999999.9
    for block in structure:
        if round((block[2] - (blocks[str(block[0])][1] / 2)), 10) < min_y:
            min_y = round((block[2] - (blocks[str(block[0])][1] / 2)), 10)
        if round((block[2] + (blocks[str(block[0])][1] / 2)), 10) > max_y:
            max_y = round((block[2] + (blocks[str(block[0])][1] / 2)), 10)
    return (round(max_y - min_y, 10))

# adds a new row of blocks to the bottom of the structure


def add_new_row(current_tree_bottom, total_tree):

    # generate possible groupings of bottom row objects
    groupings = generate_subsets(current_tree_bottom)
    # choosen block for new row
    choosen_item = choose_item(probability_table_blocks)
    center_groupings = []  # collection of viable groupings with new block at center
    edge_groupings = []  # collection of viable groupings with new block at edges
    # collection of viable groupings with new block at both center and edges
    both_groupings = []

    # check if new block is viable for each grouping in each position
    for grouping in groupings:
        if check_center(grouping, choosen_item, current_tree_bottom):  # check if center viable
            center_groupings.append(grouping)
        if check_edge(grouping, choosen_item, current_tree_bottom):  # check if edges viable
            edge_groupings.append(grouping)
        # check if both center and edges viable
        if check_both(grouping, choosen_item, current_tree_bottom):
            both_groupings.append(grouping)

    # randomly choose a configuration (grouping/placement) from the viable options
    total_options = len(center_groupings) + len(edge_groupings) + \
        len(both_groupings)  # total number of options
    if total_options > 0:
        option = randint(1, total_options)
        if option > len(center_groupings) + len(edge_groupings):
            selected_grouping = both_groupings[option -
                                               (len(center_groupings) + len(edge_groupings) + 1)]
            placement_method = 2
        elif option > len(center_groupings):
            selected_grouping = edge_groupings[option -
                                               (len(center_groupings) + 1)]
            placement_method = 1
        else:
            selected_grouping = center_groupings[option - 1]
            placement_method = 0

        # construct the new bottom row for structure using selected block/configuration
        new_bottom = []
        for subset in selected_grouping:
            if placement_method == 0:
                new_bottom.append([choosen_item, find_subset_center(subset)])
            if placement_method == 1:
                new_bottom.append([choosen_item, find_subset_edges(subset)[0]])
                new_bottom.append([choosen_item, find_subset_edges(subset)[1]])
            if placement_method == 2:
                new_bottom.append([choosen_item, find_subset_edges(subset)[0]])
                new_bottom.append([choosen_item, find_subset_center(subset)])
                new_bottom.append([choosen_item, find_subset_edges(subset)[1]])

        for i in new_bottom:
            # round all values to prevent floating point inaccuracy from causing errors
            i[1] = round(i[1], 10)

        current_tree_bottom = new_bottom
        # add new bottom row to the structure
        total_tree.append(current_tree_bottom)
        return total_tree, current_tree_bottom  # return the new structure

    else:
        # choose a new block and try again if no options available
        return add_new_row(current_tree_bottom, total_tree)

# creates the peaks (first row) of the structure


def make_peaks(center_point):

    current_tree_bottom = []  # bottom blocks of structure
    # this is the number of peaks the structure will have
    number_peaks = randint(1, max_peaks)
    # this is the item at top of structure
    top_item = choose_item(probability_table_blocks)

    if number_peaks == 1:
        current_tree_bottom.append([top_item, center_point])

    if number_peaks == 2:
        distance_apart_extra = round(
            randint(min_peak_split, max_peak_split) / 100.0, 10)
        current_tree_bottom.append([top_item, round(
            center_point - (blocks[str(top_item)][0] * 0.5) - distance_apart_extra, 10)])
        current_tree_bottom.append([top_item, round(
            center_point + (blocks[str(top_item)][0] * 0.5) + distance_apart_extra, 10)])

    if number_peaks == 3:
        distance_apart_extra = round(
            randint(min_peak_split, max_peak_split) / 100.0, 10)
        current_tree_bottom.append([top_item, round(
            center_point - (blocks[str(top_item)][0]) - distance_apart_extra, 10)])
        current_tree_bottom.append([top_item, round(center_point, 10)])
        current_tree_bottom.append([top_item, round(
            center_point + (blocks[str(top_item)][0]) + distance_apart_extra, 10)])

    if number_peaks == 4:
        distance_apart_extra = round(
            randint(min_peak_split, max_peak_split) / 100.0, 10)
        current_tree_bottom.append([top_item, round(
            center_point - (blocks[str(top_item)][0] * 1.5) - (distance_apart_extra * 2), 10)])
        current_tree_bottom.append([top_item, round(
            center_point - (blocks[str(top_item)][0] * 0.5) - distance_apart_extra, 10)])
        current_tree_bottom.append([top_item, round(
            center_point + (blocks[str(top_item)][0] * 0.5) + distance_apart_extra, 10)])
        current_tree_bottom.append([top_item, round(
            center_point + (blocks[str(top_item)][0] * 1.5) + (distance_apart_extra * 2), 10)])

    if number_peaks == 5:
        distance_apart_extra = round(
            randint(min_peak_split, max_peak_split) / 100.0, 10)
        current_tree_bottom.append([top_item, round(
            center_point - (blocks[str(top_item)][0] * 2.0) - (distance_apart_extra * 2), 10)])
        current_tree_bottom.append([top_item, round(
            center_point - (blocks[str(top_item)][0]) - distance_apart_extra, 10)])
        current_tree_bottom.append([top_item, round(center_point, 10)])
        current_tree_bottom.append([top_item, round(
            center_point + (blocks[str(top_item)][0]) + distance_apart_extra, 10)])
        current_tree_bottom.append([top_item, round(
            center_point + (blocks[str(top_item)][0] * 2.0) + (distance_apart_extra * 2), 10)])
    return current_tree_bottom

# recursively adds rows to base of strucutre until max_width or max_height is passed
# once this happens the last row added is removed and the structure is returned


def make_structure(absolute_ground, center_point, max_width, max_height, num_lvl):
    global durat_cnt
    total_tree = []  # all blocks of structure (so far)
    final_pig_positions = []
    complete_locations = []
    # creates the first row (peaks) for the structure, ensuring that max_width restriction is satisfied
    if(max_height != 0):
        current_tree_bottom = make_peaks(center_point)
        # if max_width > 0.0:
        while round(find_structure_width(current_tree_bottom)) > max_width:
            current_tree_bottom = make_peaks(center_point)

        total_tree.append(current_tree_bottom)

        # recursively add more rows of blocks to the level structure
        structure_width = find_structure_width(current_tree_bottom)
        structure_height = (blocks[str(current_tree_bottom[0][0])][1]) / 2
        if max_height > 0.0 and max_width > 0.0:
            pre_total_tree = [current_tree_bottom]
            while structure_height < max_height and structure_width < max_width:
                print("current height and freq ", structure_height, max_height)
                print("width", structure_width)
                total_tree, current_tree_bottom = add_new_row(
                    current_tree_bottom, total_tree)
                ground = absolute_ground
                for row in reversed(total_tree):
                    for item in row:
                        complete_locations.append([item[0], item[1], round(
                            (((blocks[str(item[0])][1]) / 2) + ground), 10)])
                    ground = ground + (blocks[str(item[0])][1])
                structure_height = find_structure_height(complete_locations)
                structure_width = find_structure_width(complete_locations)
                if structure_width > max_width or structure_height > max_height:
                    total_tree = deepcopy(pre_total_tree)
                else:
                    pre_total_tree = deepcopy(total_tree)

        # make structure vertically correct (add y position to blocks)
        complete_locations = []
        ground = absolute_ground
        for row in reversed(total_tree):
            for item in row:
                complete_locations.append([item[0], item[1], round(
                    (((blocks[str(item[0])][1]) / 2) + ground), 10)])
            ground = ground + (blocks[str(item[0])][1])

        print("Width:", find_structure_width(complete_locations))
        print("Height:", find_structure_height(complete_locations))
        # number blocks present in the structure
        print("Block number:", len(complete_locations))
        print("Durat cnt", durat_cnt)
        # identify all possible pig positions on top of blocks (maximum 2 pigs per block, checks center before sides)
        possible_pig_positions = []
        for block in complete_locations:
            block_width = round(blocks[str(block[0])][0], 10)
            block_height = round(blocks[str(block[0])][1], 10)
            pig_width = pig_size[0]
            pig_height = pig_size[1]

            # dont place block on edge if block too thin
            if blocks[str(block[0])][0] < pig_width:
                test_positions = [[round(block[1], 10), round(
                    block[2] + (pig_height / 2) + (block_height / 2), 10)]]
            else:
                test_positions = [[round(block[1], 10), round(block[2] + (pig_height / 2) + (block_height / 2), 10)],
                                  [round(block[1] + (block_width / 3), 10), round(
                                      block[2] + (pig_height / 2) + (block_height / 2), 10)],
                                  [round(block[1] - (block_width / 3), 10), round(block[2] + (pig_height / 2) + (block_height / 2), 10)]]  # check above centre of block
            for test_position in test_positions:
                valid_pig = True
                for i in complete_locations:
                    if (round((test_position[0] - pig_width / 2), 10) < round((i[1] + (blocks[str(i[0])][0]) / 2), 10) and
                        round((test_position[0] + pig_width / 2), 10) > round((i[1] - (blocks[str(i[0])][0]) / 2), 10) and
                        round((test_position[1] + pig_height / 2), 10) > round((i[2] - (blocks[str(i[0])][1]) / 2), 10) and
                            round((test_position[1] - pig_height / 2), 10) < round((i[2] + (blocks[str(i[0])][1]) / 2), 10)):
                        valid_pig = False
                if valid_pig == True:
                    possible_pig_positions.append(test_position)

        # identify all possible pig positions on ground within structure
        left_bottom = total_tree[-1][0]
        right_bottom = total_tree[-1][-1]
        test_positions = []
        x_pos = left_bottom[1]

        while x_pos < right_bottom[1]:
            test_positions.append([round(x_pos, 10), round(
                absolute_ground + (pig_height / 2), 10)])
            x_pos = x_pos + pig_precision

        for test_position in test_positions:
            valid_pig = True
            for i in complete_locations:
                if (round((test_position[0] - pig_width / 2), 10) < round((i[1] + (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[0] + pig_width / 2), 10) > round((i[1] - (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[1] + pig_height / 2), 10) > round((i[2] - (blocks[str(i[0])][1]) / 2), 10) and
                        round((test_position[1] - pig_height / 2), 10) < round((i[2] + (blocks[str(i[0])][1]) / 2), 10)):
                    valid_pig = False
            if valid_pig == True:
                possible_pig_positions.append(test_position)

        # randomly choose a pig position and remove those that overlap it, repeat until no more valid positions
        while len(possible_pig_positions) > 0:
            pig_choice = possible_pig_positions.pop(
                randint(1, len(possible_pig_positions)) - 1)
            final_pig_positions.append(pig_choice)
            new_pig_positions = []
            for i in possible_pig_positions:
                if (round((pig_choice[0] - pig_width / 2), 10) >= round((i[0] + pig_width / 2), 10) or
                    round((pig_choice[0] + pig_width / 2), 10) <= round((i[0] - pig_width / 2), 10) or
                    round((pig_choice[1] + pig_height / 2), 10) <= round((i[1] - pig_height / 2), 10) or
                        round((pig_choice[1] - pig_height / 2), 10) >= round((i[1] + pig_height / 2), 10)):
                    new_pig_positions.append(i)
            possible_pig_positions = new_pig_positions

        # number of pigs present in the structure
        print("Pig number:", len(final_pig_positions))
        print("")
    durat_cnt += 1
    if(durat_cnt >= len(durats[num_lvl]) - 1):
        durat_cnt = 0
    return complete_locations, final_pig_positions

# divide the available ground space between the chosen number of ground structures


def create_ground_structures(num_lvl):
    ground_divides = []
    if number_ground_structures > 0:
        ground_divides = [level_width_min, level_width_max]
    for i in range(number_ground_structures - 1):
        ground_divides.insert(i + 1, ground_divides[i] + durats[num_lvl][i])

    # determine the area available to each ground structure
    ground_positions = []
    ground_widths = []
    for j in range(len(ground_divides) - 1):
        ground_positions.append(
            ground_divides[j] + ((ground_divides[j + 1] - ground_divides[j]) / 2))
        ground_widths.append(ground_divides[j + 1] - ground_divides[j])

    print("number of ground structures:", len(ground_positions))
    print("")

    # creates a ground structure for each defined area
    complete_locations = []
    final_pig_positions = []
    print("The ground positions:")
    for i in range(len(ground_positions)):
        print(str(i) + ")" + str(ground_positions[i]))
        max_width = ground_widths[i]
        max_height = -7
        print("frequencies list:")
        print(freqs[num_lvl])
        print("durations list:")
        print(durats[num_lvl])
        print(durat_cnt)
        if(isinstance(freqs[num_lvl][durat_cnt], list)):
            max_height = freqs[num_lvl][durat_cnt][0]
        else:
            max_height = freqs[num_lvl][durat_cnt]
        print("max height is" + str(max_height))
        center_point = ground_positions[i]
        complete_locations2, final_pig_positions2 = make_structure(
            absolute_ground, center_point, max_width, max_height, num_lvl)
        complete_locations = complete_locations + complete_locations2
        final_pig_positions = final_pig_positions + final_pig_positions2
    total_ground_pos.append(ground_positions)
    return len(ground_positions), complete_locations, final_pig_positions

# creates a set number of platforms within the level
# automatically reduced if space not found after set number of attempts


def create_platforms(number_platforms, complete_locations, final_pig_positions, num_lvl):

    platform_centers = []
    attempts = 0  # number of attempts so far to find space for platform
    final_platforms = []
    for i in range(len(total_ground_pos[num_lvl])):
        print("total_ground_pos")
        print(total_ground_pos[num_lvl][i])
    while len(final_platforms) < number_platforms:
        platform_width = int(
            freqs[num_lvl][platform_indexes[num_lvl][len(final_platforms)]][1] + 1)
        platform_position = [total_ground_pos[num_lvl][platform_indexes[num_lvl][len(final_platforms)]],
                             uniform(level_height_min, (level_height_max - minimum_height_gap))]
        temp_platform = []

        if platform_width == 1:
            temp_platform.append(platform_position)

        if platform_width == 2:
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 0.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 0.5), platform_position[1]])

        if platform_width == 3:
            temp_platform.append(
                [platform_position[0] - (platform_size[0]), platform_position[1]])
            temp_platform.append(platform_position)
            temp_platform.append(
                [platform_position[0] + (platform_size[0]), platform_position[1]])

        if platform_width == 4:
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 1.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 0.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 0.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 1.5), platform_position[1]])

        if platform_width == 5:
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 2.0), platform_position[1]])
            temp_platform.append(
                [platform_position[0] - (platform_size[0]), platform_position[1]])
            temp_platform.append(platform_position)
            temp_platform.append(
                [platform_position[0] + (platform_size[0]), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 2.0), platform_position[1]])

        if platform_width == 6:
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 2.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 1.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 0.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 0.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 1.5), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 2.5), platform_position[1]])

        if platform_width == 7:
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 3.0), platform_position[1]])
            temp_platform.append(
                [platform_position[0] - (platform_size[0] * 2.0), platform_position[1]])
            temp_platform.append(
                [platform_position[0] - (platform_size[0]), platform_position[1]])
            temp_platform.append(platform_position)
            temp_platform.append(
                [platform_position[0] + (platform_size[0]), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 2.0), platform_position[1]])
            temp_platform.append(
                [platform_position[0] + (platform_size[0] * 3.0), platform_position[1]])

        overlap = False
        for platform in temp_platform:

            if (((platform[0] - (platform_size[0] / 2)) < level_width_min) or ((platform[0] + (platform_size[0]) / 2) > level_width_max)):
                overlap = True

            for block in complete_locations:
                if (round((platform[0] - platform_distance_buffer - platform_size[0] / 2), 10) <= round((block[1] + blocks[str(block[0])][0] / 2), 10) and
                    round((platform[0] + platform_distance_buffer + platform_size[0] / 2), 10) >= round((block[1] - blocks[str(block[0])][0] / 2), 10) and
                    round((platform[1] + platform_distance_buffer + platform_size[1] / 2), 10) >= round((block[2] - blocks[str(block[0])][1] / 2), 10) and
                        round((platform[1] - platform_distance_buffer - platform_size[1] / 2), 10) <= round((block[2] + blocks[str(block[0])][1] / 2), 10)):
                    overlap = True

            for pig in final_pig_positions:
                if (round((platform[0] - platform_distance_buffer - platform_size[0] / 2), 10) <= round((pig[0] + pig_size[0] / 2), 10) and
                    round((platform[0] + platform_distance_buffer + platform_size[0] / 2), 10) >= round((pig[0] - pig_size[0] / 2), 10) and
                    round((platform[1] + platform_distance_buffer + platform_size[1] / 2), 10) >= round((pig[1] - pig_size[1] / 2), 10) and
                        round((platform[1] - platform_distance_buffer - platform_size[1] / 2), 10) <= round((pig[1] + pig_size[1] / 2), 10)):
                    overlap = True

            for platform_set in final_platforms:
                for platform2 in platform_set:
                    if (round((platform[0] - platform_distance_buffer - platform_size[0] / 2), 10) <= round((platform2[0] + platform_size[0] / 2), 10) and
                        round((platform[0] + platform_distance_buffer + platform_size[0] / 2), 10) >= round((platform2[0] - platform_size[0] / 2), 10) and
                        round((platform[1] + platform_distance_buffer + platform_size[1] / 2), 10) >= round((platform2[1] - platform_size[1] / 2), 10) and
                            round((platform[1] - platform_distance_buffer - platform_size[1] / 2), 10) <= round((platform2[1] + platform_size[1] / 2), 10)):
                        overlap = True

            for platform_set2 in final_platforms:
                for i in platform_set2:
                    if i[0] + platform_size[0] > platform[0] and i[0] - platform_size[0] < platform[0]:
                        if i[1] + minimum_height_gap > platform[1] and i[1] - minimum_height_gap < platform[1]:
                            overlap = True

        if overlap == False:
            final_platforms.append(temp_platform)
            platform_centers.append(platform_position)

        # The following 4 lines are the reason why even if the double note possibility is %100, there aren't always that many platform structures.
        attempts = attempts + 1
        if attempts > max_attempts:
            attempts = 0
            number_platforms = number_platforms - 1

    print("number platforms:", number_platforms)
    print("")

    return number_platforms, final_platforms, platform_centers

# create sutiable structures for each platform


def create_platform_structures(final_platforms, platform_centers, complete_locations, final_pig_positions, num_lvl):
    current_platform = 0
    for platform_set in final_platforms:
        platform_set_width = len(platform_set) * platform_size[0]

        above_blocks = []
        for platform_set2 in final_platforms:
            if platform_set2 != platform_set:
                for i in platform_set2:
                    if i[0] + platform_size[0] > platform_set[0][0] and i[0] - platform_size[0] < platform_set[-1][0] and i[1] > platform_set[0][1]:
                        above_blocks.append(i)

        min_above = level_height_max
        for j in above_blocks:
            if j[1] < min_above:
                min_above = j[1]

        center_point = platform_centers[current_platform][0]
        absolute_ground = platform_centers[current_platform][1] + \
            (platform_size[1] / 2)

        max_width = platform_set_width
        max_height = (min_above - absolute_ground) - \
            pig_size[1] - platform_size[1]

        complete_locations2, final_pig_positions2 = make_structure(
            absolute_ground, center_point, max_width, max_height, num_lvl)
        complete_locations = complete_locations + complete_locations2
        final_pig_positions = final_pig_positions + final_pig_positions2

        current_platform = current_platform + 1

    return complete_locations, final_pig_positions

# remove random pigs until number equals the desired amount


def remove_unnecessary_pigs(number_pigs):
    removed_pigs = []
    while len(final_pig_positions) > number_pigs:
        remove_pos = randint(0, len(final_pig_positions) - 1)
        removed_pigs.append(final_pig_positions[remove_pos])
        final_pig_positions.pop(remove_pos)
    return final_pig_positions, removed_pigs

# add pigs on the ground until number equals the desired amount


def add_necessary_pigs(number_pigs):
    while len(final_pig_positions) < number_pigs:
        test_position = [
            uniform(level_width_min, level_width_max), absolute_ground]
        pig_width = pig_size[0]
        pig_height = pig_size[1]
        valid_pig = True
        for i in complete_locations:
            if (round((test_position[0] - pig_width / 2), 10) < round((i[1] + (blocks[str(i[0])][0]) / 2), 10) and
                round((test_position[0] + pig_width / 2), 10) > round((i[1] - (blocks[str(i[0])][0]) / 2), 10) and
                round((test_position[1] + pig_height / 2), 10) > round((i[2] - (blocks[str(i[0])][1]) / 2), 10) and
                    round((test_position[1] - pig_height / 2), 10) < round((i[2] + (blocks[str(i[0])][1]) / 2), 10)):
                valid_pig = False
        for i in final_pig_positions:
            if (round((test_position[0] - pig_width / 2), 10) < round((i[0] + (pig_width / 2)), 10) and
                round((test_position[0] + pig_width / 2), 10) > round((i[0] - (pig_width / 2)), 10) and
                round((test_position[1] + pig_height / 2), 10) > round((i[1] - (pig_height / 2)), 10) and
                    round((test_position[1] - pig_height / 2), 10) < round((i[1] + (pig_height / 2)), 10)):
                valid_pig = False
        if valid_pig == True:
            final_pig_positions.append(test_position)
    return final_pig_positions

# choose the number of birds based on the number of pigs and structures present within level


def choose_number_birds(final_pig_positions, number_ground_structures, number_platforms):
    number_birds = int(ceil(len(final_pig_positions) / 2))
    if (number_ground_structures + number_platforms) >= number_birds:
        number_birds = number_birds + 1
    number_birds = number_birds + 1  # adjust based on desired difficulty
    return number_birds

# identify all possible triangleHole positions on top of blocks


def find_trihole_positions(complete_locations):
    possible_trihole_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        trihole_width = additional_object_sizes['1'][0]
        trihole_height = additional_object_sizes['1'][1]

        # don't place block on edge if block too thin
        if blocks[str(block[0])][0] < trihole_width:
            test_positions = [[round(block[1], 10), round(
                block[2] + (trihole_height / 2) + (block_height / 2), 10)]]
        else:
            test_positions = [[round(block[1], 10), round(block[2] + (trihole_height / 2) + (block_height / 2), 10)],
                              [round(block[1] + (block_width / 3), 10), round(block[2] +
                                                                              (trihole_height / 2) + (block_height / 2), 10)],
                              [round(block[1] - (block_width / 3), 10), round(block[2] + (trihole_height / 2) + (block_height / 2), 10)]]

        for test_position in test_positions:
            valid_position = True
            for i in complete_locations:
                if (round((test_position[0] - trihole_width / 2), 10) < round((i[1] + (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[0] + trihole_width / 2), 10) > round((i[1] - (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[1] + trihole_height / 2), 10) > round((i[2] - (blocks[str(i[0])][1]) / 2), 10) and
                        round((test_position[1] - trihole_height / 2), 10) < round((i[2] + (blocks[str(i[0])][1]) / 2), 10)):
                    valid_position = False
            for j in final_pig_positions:
                if (round((test_position[0] - trihole_width / 2), 10) < round((j[0] + (pig_size[0] / 2)), 10) and
                    round((test_position[0] + trihole_width / 2), 10) > round((j[0] - (pig_size[0] / 2)), 10) and
                    round((test_position[1] + trihole_height / 2), 10) > round((j[1] - (pig_size[1] / 2)), 10) and
                        round((test_position[1] - trihole_height / 2), 10) < round((j[1] + (pig_size[1] / 2)), 10)):
                    valid_position = False
            for j in final_TNT_positions:
                if (round((test_position[0] - trihole_width / 2), 10) < round((j[0] + (pig_size[0] / 2)), 10) and
                    round((test_position[0] + trihole_width / 2), 10) > round((j[0] - (pig_size[0] / 2)), 10) and
                    round((test_position[1] + trihole_height / 2), 10) > round((j[1] - (pig_size[1] / 2)), 10) and
                        round((test_position[1] - trihole_height / 2), 10) < round((j[1] + (pig_size[1] / 2)), 10)):
                    valid_position = False
            for i in final_platforms:
                for j in i:
                    if (round((test_position[0] - trihole_width/2), 10) < round((j[0] + (platform_size[0]/2)), 10) and
                        round((test_position[0] + trihole_width/2), 10) > round((j[0] - (platform_size[0]/2)), 10) and
                        round((test_position[1] + platform_distance_buffer + trihole_height/2), 10) > round((j[1] - (platform_size[1]/2)), 10) and
                            round((test_position[1] - platform_distance_buffer - trihole_height/2), 10) < round((j[1] + (platform_size[1]/2)), 10)):
                        valid_position = False
            if valid_position == True:
                possible_trihole_positions.append(test_position)

    return possible_trihole_positions

# identify all possible triangle positions on top of blocks


def find_tri_positions(complete_locations):
    possible_tri_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        tri_width = additional_object_sizes['2'][0]
        tri_height = additional_object_sizes['2'][1]

        # don't place block on edge if block too thin
        if blocks[str(block[0])][0] < tri_width:
            test_positions = [[round(block[1], 10), round(
                block[2] + (tri_height / 2) + (block_height / 2), 10)]]
        else:
            test_positions = [[round(block[1], 10), round(block[2] + (tri_height / 2) + (block_height / 2), 10)],
                              [round(block[1] + (block_width / 3), 10), round(block[2] +
                                                                              (tri_height / 2) + (block_height / 2), 10)],
                              [round(block[1] - (block_width / 3), 10), round(block[2] + (tri_height / 2) + (block_height / 2), 10)]]

        for test_position in test_positions:
            valid_position = True
            for i in complete_locations:
                if (round((test_position[0] - tri_width / 2), 10) < round((i[1] + (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[0] + tri_width / 2), 10) > round((i[1] - (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[1] + tri_height / 2), 10) > round((i[2] - (blocks[str(i[0])][1]) / 2), 10) and
                        round((test_position[1] - tri_height / 2), 10) < round((i[2] + (blocks[str(i[0])][1]) / 2), 10)):
                    valid_position = False
            for j in final_pig_positions:
                if (round((test_position[0] - tri_width / 2), 100) < round((j[0] + (pig_size[0] / 2)), 100) and
                    round((test_position[0] + tri_width / 2), 100) > round((j[0] - (pig_size[0] / 2)), 100) and
                    round((test_position[1] + tri_height / 2), 100) > round((j[1] - (pig_size[1] / 2)), 100) and
                        round((test_position[1] - tri_height / 2), 100) < round((j[1] + (pig_size[1] / 2)), 100)):
                    valid_position = False
            for j in final_TNT_positions:
                if (round((test_position[0] - tri_width / 2), 100) < round((j[0] + (pig_size[0] / 2)), 100) and
                    round((test_position[0] + tri_width / 2), 100) > round((j[0] - (pig_size[0] / 2)), 100) and
                    round((test_position[1] + tri_height / 2), 100) > round((j[1] - (pig_size[1] / 2)), 100) and
                        round((test_position[1] - tri_height / 2), 100) < round((j[1] + (pig_size[1] / 2)), 100)):
                    valid_position = False
            for i in final_platforms:
                for j in i:
                    if (round((test_position[0] - tri_width/2), 10) < round((j[0] + (platform_size[0]/2)), 10) and
                        round((test_position[0] + tri_width/2), 10) > round((j[0] - (platform_size[0]/2)), 10) and
                        round((test_position[1] + platform_distance_buffer + tri_height/2), 10) > round((j[1] - (platform_size[1]/2)), 10) and
                            round((test_position[1] - platform_distance_buffer - tri_height/2), 10) < round((j[1] + (platform_size[1]/2)), 10)):
                        valid_position = False

            # as block not symmetrical need to check for support
            if blocks[str(block[0])][0] < tri_width:
                valid_position = False
            if valid_position == True:
                possible_tri_positions.append(test_position)

    return possible_tri_positions

# identify all possible circle positions on top of blocks (can only be placed in middle of block)


def find_cir_positions(complete_locations):
    possible_cir_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        cir_width = additional_object_sizes['3'][0]
        cir_height = additional_object_sizes['3'][1]

        # only checks above block's center
        test_positions = [[round(block[1], 10), round(
            block[2] + (cir_height / 2) + (block_height / 2), 10)]]

        for test_position in test_positions:
            valid_position = True
            for i in complete_locations:
                if (round((test_position[0] - cir_width / 2), 10) < round((i[1] + (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[0] + cir_width / 2), 10) > round((i[1] - (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[1] + cir_height / 2), 10) > round((i[2] - (blocks[str(i[0])][1]) / 2), 10) and
                        round((test_position[1] - cir_height / 2), 10) < round((i[2] + (blocks[str(i[0])][1]) / 2), 10)):
                    valid_position = False
            for j in final_pig_positions:
                if (round((test_position[0] - cir_width / 2), 10) < round((j[0] + (pig_size[0] / 2)), 10) and
                    round((test_position[0] + cir_width / 2), 10) > round((j[0] - (pig_size[0] / 2)), 10) and
                    round((test_position[1] + cir_height / 2), 10) > round((j[1] - (pig_size[1] / 2)), 10) and
                        round((test_position[1] - cir_height / 2), 10) < round((j[1] + (pig_size[1] / 2)), 10)):
                    valid_position = False
            for j in final_TNT_positions:
                if (round((test_position[0] - cir_width / 2), 10) < round((j[0] + (pig_size[0] / 2)), 10) and
                    round((test_position[0] + cir_width / 2), 10) > round((j[0] - (pig_size[0] / 2)), 10) and
                    round((test_position[1] + cir_height / 2), 10) > round((j[1] - (pig_size[1] / 2)), 10) and
                        round((test_position[1] - cir_height / 2), 10) < round((j[1] + (pig_size[1] / 2)), 10)):
                    valid_position = False
            for i in final_platforms:
                for j in i:
                    if (round((test_position[0] - cir_width/2), 10) < round((j[0] + (platform_size[0]/2)), 10) and
                        round((test_position[0] + cir_width/2), 10) > round((j[0] - (platform_size[0]/2)), 10) and
                        round((test_position[1] + platform_distance_buffer + cir_height/2), 10) > round((j[1] - (platform_size[1]/2)), 10) and
                            round((test_position[1] - platform_distance_buffer - cir_height/2), 10) < round((j[1] + (platform_size[1]/2)), 10)):
                        valid_position = False
            if valid_position == True:
                possible_cir_positions.append(test_position)

    return possible_cir_positions

# identify all possible circleSmall positions on top of blocks


def find_cirsmall_positions(complete_locations):
    possible_cirsmall_positions = []
    for block in complete_locations:
        block_width = round(blocks[str(block[0])][0], 10)
        block_height = round(blocks[str(block[0])][1], 10)
        cirsmall_width = additional_object_sizes['4'][0]
        cirsmall_height = additional_object_sizes['4'][1]

        # don't place block on edge if block too thin
        if blocks[str(block[0])][0] < cirsmall_width:
            test_positions = [[round(block[1], 10), round(
                block[2] + (cirsmall_height / 2) + (block_height / 2), 10)]]
        else:
            test_positions = [[round(block[1], 10), round(block[2] + (cirsmall_height / 2) + (block_height / 2), 10)],
                              [round(block[1] + (block_width / 3), 10), round(block[2] +
                                                                              (cirsmall_height / 2) + (block_height / 2), 10)],
                              [round(block[1] - (block_width / 3), 10), round(block[2] + (cirsmall_height / 2) + (block_height / 2), 10)]]

        for test_position in test_positions:
            valid_position = True
            for i in complete_locations:
                if (round((test_position[0] - cirsmall_width / 2), 10) < round((i[1] + (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[0] + cirsmall_width / 2), 10) > round((i[1] - (blocks[str(i[0])][0]) / 2), 10) and
                    round((test_position[1] + cirsmall_height / 2), 10) > round((i[2] - (blocks[str(i[0])][1]) / 2), 10) and
                        round((test_position[1] - cirsmall_height / 2), 10) < round((i[2] + (blocks[str(i[0])][1]) / 2), 10)):
                    valid_position = False
            for j in final_pig_positions:
                if (round((test_position[0] - cirsmall_width / 2), 10) < round((j[0] + (pig_size[0] / 2)), 10) and
                    round((test_position[0] + cirsmall_width / 2), 10) > round((j[0] - (pig_size[0] / 2)), 10) and
                    round((test_position[1] + cirsmall_height / 2), 10) > round((j[1] - (pig_size[1] / 2)), 10) and
                        round((test_position[1] - cirsmall_height / 2), 10) < round((j[1] + (pig_size[1] / 2)), 10)):
                    valid_position = False
            for j in final_TNT_positions:
                if (round((test_position[0] - cirsmall_width / 2), 10) < round((j[0] + (pig_size[0] / 2)), 10) and
                    round((test_position[0] + cirsmall_width / 2), 10) > round((j[0] - (pig_size[0] / 2)), 10) and
                    round((test_position[1] + cirsmall_height / 2), 10) > round((j[1] - (pig_size[1] / 2)), 10) and
                        round((test_position[1] - cirsmall_height / 2), 10) < round((j[1] + (pig_size[1] / 2)), 10)):
                    valid_position = False
            for i in final_platforms:
                for j in i:
                    if (round((test_position[0] - cirsmall_width/2), 10) < round((j[0] + (platform_size[0]/2)), 10) and
                        round((test_position[0] + cirsmall_width/2), 10) > round((j[0] - (platform_size[0]/2)), 10) and
                        round((test_position[1] + platform_distance_buffer + cirsmall_height/2), 10) > round((j[1] - (platform_size[1]/2)), 10) and
                            round((test_position[1] - platform_distance_buffer - cirsmall_height/2), 10) < round((j[1] + (platform_size[1]/2)), 10)):
                        valid_position = False
            if valid_position == True:
                possible_cirsmall_positions.append(test_position)

    return possible_cirsmall_positions

# finds possible positions for valid additional block types


def find_additional_block_positions(complete_locations):
    possible_trihole_positions = []
    possible_tri_positions = []
    possible_cir_positions = []
    possible_cirsmall_positions = []
    if trihole_allowed == True:
        possible_trihole_positions = find_trihole_positions(complete_locations)
    if tri_allowed == True:
        possible_tri_positions = find_tri_positions(complete_locations)
    if cir_allowed == True:
        possible_cir_positions = find_cir_positions(complete_locations)
    if cirsmall_allowed == True:
        possible_cirsmall_positions = find_cirsmall_positions(
            complete_locations)
    return possible_trihole_positions, possible_tri_positions, possible_cir_positions, possible_cirsmall_positions

# combine all possible additonal block positions into one set


def add_additional_blocks(possible_trihole_positions, possible_tri_positions, possible_cir_positions, possible_cirsmall_positions):
    all_other = []
    for i in possible_trihole_positions:
        all_other.append(['1', i[0], i[1]])
    for i in possible_tri_positions:
        all_other.append(['2', i[0], i[1]])
    for i in possible_cir_positions:
        all_other.append(['3', i[0], i[1]])
    for i in possible_cirsmall_positions:
        all_other.append(['4', i[0], i[1]])

    # randomly choose an additional block position and remove those that overlap it
    # repeat untill no more valid position

    selected_other = []
    while (len(all_other) > 0):
        chosen = all_other.pop(randint(0, len(all_other) - 1))
        selected_other.append(chosen)
        new_all_other = []
        for i in all_other:
            if (round((chosen[1] - (additional_object_sizes[chosen[0]][0] / 2)), 10) >= round((i[1] + (additional_object_sizes[i[0]][0] / 2)), 10) or
                round((chosen[1] + (additional_object_sizes[chosen[0]][0] / 2)), 10) <= round((i[1] - (additional_object_sizes[i[0]][0] / 2)), 10) or
                round((chosen[2] + (additional_object_sizes[chosen[0]][1] / 2)), 10) <= round((i[2] - (additional_object_sizes[i[0]][1] / 2)), 10) or
                    round((chosen[2] - (additional_object_sizes[chosen[0]][1] / 2)), 10) >= round((i[2] + (additional_object_sizes[i[0]][1] / 2)), 10)):
                new_all_other.append(i)
        all_other = new_all_other

    return selected_other

# remove restricted block types from the available selection


def remove_blocks(restricted_blocks):
    total_prob_removed = 0.0
    new_prob_table = deepcopy(probability_table_blocks)
    for block_name in restricted_blocks:
        for key, value in block_names.items():
            if value == block_name:
                total_prob_removed = total_prob_removed + \
                    probability_table_blocks[key]
                new_prob_table[key] = 0.0
    new_total = 1.0 - total_prob_removed
    for key, value in new_prob_table.items():
        new_prob_table[key] = value / new_total
    return new_prob_table

# add TNT blocks based on removed pig positions


def add_TNT(potential_positions):
    final_TNT_positions = []
    for position in potential_positions:
        if (uniform(0.0, 1.0) < TNT_block_probability):
            final_TNT_positions.append(position)
    return final_TNT_positions

# write level out in desired xml format


def write_level_xml(complete_locations, selected_other, final_pig_positions, final_TNT_positions, final_platforms, number_birds, current_level, restricted_combinations):

    f = open("level-%s.xml" % current_level, "w")

    f.write('<?xml version="1.0" encoding="utf-16"?>\n')
    f.write('<Level width ="2">\n')
    f.write('<Camera x="0" y="2" minWidth="20" maxWidth="30">\n')
    f.write('<Birds>\n')
    for i in range(number_birds):  # bird type is chosen using probability table
        f.write('<Bird type="%s"/>\n' %
                bird_names[str(choose_item(bird_probabilities))])
    f.write('</Birds>\n')
    f.write('<Slingshot x="-8" y="-2.5">\n')
    f.write('<GameObjects>\n')

    for i in complete_locations:
        # material is chosen randomly
        material = materials[randint(0, len(materials) - 1)]
        # if material if not allowed for block type then pick again
        while [material, block_names[str(i[0])]] in restricted_combinations:
            material = materials[randint(0, len(materials) - 1)]
        rotation = 0
        if (i[0] in (3, 7, 9, 11, 13)):
            rotation = 90
        f.write('<Block type="%s" material="%s" x="%s" y="%s" rotation="%s" />\n' %
                (block_names[str(i[0])], material, str(i[1]), str(i[2]), str(rotation)))

    for i in selected_other:
        # material is chosen randomly
        material = materials[randint(0, len(materials) - 1)]
        # if material if not allowed for block type then pick again
        while [material, additional_objects[str(i[0])]] in restricted_combinations:
            material = materials[randint(0, len(materials) - 1)]
        if i[0] == '2':
            facing = randint(0, 1)
            f.write('<Block type="%s" material="%s" x="%s" y="%s" rotation="%s" />\n' %
                    (additional_objects[i[0]], material, str(i[1]), str(i[2]), str(facing * 90.0)))
        else:
            f.write('<Block type="%s" material="%s" x="%s" y="%s" rotation="0" />\n' %
                    (additional_objects[i[0]], material, str(i[1]), str(i[2])))

    for i in final_pig_positions:
        f.write('<Pig type="BasicSmall" material="" x="%s" y="%s" rotation="0" />\n' %
                (str(i[0]), str(i[1])))

    for i in final_platforms:
        for j in i:
            f.write('<Platform type="Platform" material="" x="%s" y="%s" />\n' %
                    (str(j[0]), str(j[1])))

    for i in final_TNT_positions:
        f.write('<TNT type="" material="" x="%s" y="%s" rotation="0" />\n' %
                (str(i[0]), str(i[1])))

    f.write('</GameObjects>\n')
    f.write('</Level>\n')

    f.close()

# generate levels using input parameters


backup_probability_table_blocks = deepcopy(probability_table_blocks)
backup_materials = deepcopy(materials)

FILE = open("parameters.txt", 'r')
checker = FILE.readline()
finished_levels = 0
while (checker != ""):
    if checker == "\n":
        checker = FILE.readline()
    else:
        # the number of levels to generate
        number_levels = int(deepcopy(checker))
        # block type and material combination that are banned from the level
        restricted_combinations = FILE.readline().split(',')
        for i in range(len(restricted_combinations)):
            # if all materials are baned for a block type then do not use that block type
            restricted_combinations[i] = restricted_combinations[i].split()
        pig_range = FILE.readline().split(',')
        # time limit to create the levels, shouldn't be an issue for most generators (approximately an hour for 10 levels)
        time_limit = int(FILE.readline())
        checker = FILE.readline()

        restricted_blocks = []  # block types that cannot be used with any materials
        for key, value in block_names.items():
            completely_restricted = True
            for material in materials:
                if [material, value] not in restricted_combinations:
                    completely_restricted = False
            if completely_restricted == True:
                restricted_blocks.append(value)

        probability_table_blocks = deepcopy(backup_probability_table_blocks)
        trihole_allowed = True
        tri_allowed = True
        cir_allowed = True
        cirsmall_allowed = True
        TNT_allowed = True

        # remove restricted block types from the structure generation process
        probability_table_blocks = remove_blocks(restricted_blocks)
        if "TriangleHole" in restricted_blocks:
            trihole_allowed = False
        if "Triangle" in restricted_blocks:
            tri_allowed = False
        if "Circle" in restricted_blocks:
            cir_allowed = False
        if "CircleSmall" in restricted_blocks:
            cirsmall_allowed = False

        all_tone_check()
        tonal_tone_check()
        rest_check()
        double_note_check()
        rest_adjust()

        for current_level in range(number_levels):
            generate_stream(current_level)
            num_platforms = len(platform_indexes[current_level])
            # number of ground structures
            number_ground_structures = len(durats[current_level])
            # number of platforms (reduced automatically if not enough space)
            number_platforms = num_platforms
            # number of pigs (if set too large then can cause program to infinitely loop)
            number_pigs = randint(int(pig_range[0]), int(pig_range[1]))

            if (current_level + finished_levels + 4) < 10:
                level_name = "0" + str(current_level + finished_levels + 4)
            else:
                level_name = str(current_level + finished_levels + 4)

            final_platforms = 0
            number_ground_structures, complete_locations, final_pig_positions = create_ground_structures(
                current_level)
            number_platforms, final_platforms, platform_centers = create_platforms(
                number_platforms, complete_locations, final_pig_positions, current_level)
            complete_locations, final_pig_positions = create_platform_structures(
                final_platforms, platform_centers, complete_locations, final_pig_positions, current_level)
            final_pig_positions, removed_pigs = remove_unnecessary_pigs(
                number_pigs)
            final_pig_positions = add_necessary_pigs(number_pigs)
            final_TNT_positions = add_TNT(removed_pigs)
            number_birds = choose_number_birds(
                final_pig_positions, number_ground_structures, number_platforms)
            possible_trihole_positions, possible_tri_positions, possible_cir_positions, possible_cirsmall_positions = find_additional_block_positions(
                complete_locations)
            selected_other = add_additional_blocks(
                possible_trihole_positions, possible_tri_positions, possible_cir_positions, possible_cirsmall_positions)
            write_level_xml(complete_locations, selected_other, final_pig_positions, final_TNT_positions,
                            final_platforms, number_birds, level_name, restricted_combinations)
        finished_levels = finished_levels + number_levels
