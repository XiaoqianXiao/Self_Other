# -*- coding: utf-8 -*-
"""
Written by Jonas Kristoffer Lindeløv, lindeloev.net.

TO DO:
 * Control stimulus appearance using variables?
 * Set fullscreen
"""

# Measure this on your monitor
MON_WIDTH = 37  # cm
MON_DISTANCE = 70  # cm
MON_SIZE = [1024, 768]  # x,y pixels

# Presentation parameters
SCAN_TIME = 2.5  # number of seconds
SCAN_TIME_BUFFER = 0.5  # seconds to wait before concluding that the scanner won't send more triggers
NONRESPONSE_WINDOW = 0.0  # how many seconds to ignore responses in the beginning of a trial

FIXATION_SIZE = 0.5
TEXT_SIZE = 0.7   # height of the letters in degrees visual angle
TEXT_DISTANCE = 0.7  # vertical distance from text to fixation cross in degrees visual angle
INSTRUCTIONS = {
    'break': u'',  # displayed during breaks
    'SCANNER': u'',  # Instructions in scanner. Note that key name should match DIALOGUE['setting']
    'PRACTICE': u"""
IN THE FOLLOWING TASK, YOU WILL BE ASKED TO RATE ONE OF THREE TYPES OF JUDGMENTS FOR DIFFERENT WORDS:

SELF: DOES THIS WORD DESCRIBE YOU?
OBAMA: DOES THIS WORD DESCRIBE FORMER U.S. PRESIDENT BARACK OBAMA?
UPPERCASE: IS THIS WORD PRINTED IN UPPERCASE LETTERS?

FOR EACH ITEM, PLEASE RESPOND WITH YES [1] OR NO [2] ON YOUR RESPONSE BOX. PLEASE KEEP YOUR EYES ON THE CENTRAL FIXATION POINT DURING THE TASK. IF THE NEXT TRIAL COMES UP AND YOU HAVE NOT YET RESPONDED TO THE PREVIOUS TRIAL, THAT'S OKAY, JUST SKIP IT AND MOVE ONTO THE NEXT ONE. 

READY?"""
}

# Keyboard keys
KEYS_SUBJECT = {'1': 'yes', '2': 'no'}
KEYS_EXPERIMENTER = ['space']
SCANNER_KEYS = ['=', 'equal']
QUIT_KEYS = ['f9']

conditions = ['SELF', 'OBAMA', 'UPPERCASE']
ORDER_FILES = ['SelfOther-001.txt', 'SelfOther-002.txt', 'SelfOther-003.txt']

JUDGEMENT_MAP = {  # mapping from sequence to judgement type (fixed for all)
    'NULL':'NULL', 
    'evt1':'SELF', 
    'evt2':'UPPERCASE',
    'evt3':'OBAMA'
}


"""
SET THINGS UP
"""
from psychopy import visual, event, core, gui, monitors
import itertools
import math
import random
from datetime import datetime
from pytz import timezone
import pandas as pd

# Dialogue box
DIALOGUE = {
    'order_id': range(6),
    'id': '',
    'age': '',
    'session': '',
    'setting': ['SCANNER', 'PRACTICE'],
    'words_file': ['Lists 1-3 run 1.xlsx', 'Lists 1-3 run 2.xlsx', 'Lists 1-3 run 3.xlsx', 'Lists 4-6 run 1.xlsx', 'Lists 4-6 run 2.xlsx', 'Lists 4-6 run 3.xlsx', 'Word Lists 1-3.xlsx','Word Lists 4-6.xlsx', 'PRACTICE.xlsx'],
    'start_run': [1,2,3]}
if not gui.DlgFromDict(DIALOGUE, order=['id', 'age', 'session', 'setting', 'order_id', 'start_run']).OK:
    core.quit() 
DIALOGUE['order_id'] = int(DIALOGUE['order_id'])
DIALOGUE['start_run'] = int(DIALOGUE['start_run'])

# Psychopy window
my_monitor = monitors.Monitor('testMonitor', width=MON_WIDTH, distance=MON_DISTANCE)  # Create monitor object from the variables above. This is needed to control size of stimuli in degrees.
my_monitor.setSizePix(MON_SIZE)
win = visual.Window(monitor=my_monitor, color=(-1,-1,-1), units='deg', fullscr=True, allowGUI=True)

# Psychopy stimuli/objects
fix = visual.TextStim(win, text='+', height=FIXATION_SIZE, font='Geneva', bold=True)
text_judgement = visual.TextStim(win, pos=(0, TEXT_DISTANCE), height=TEXT_SIZE, font='Geneva', bold=True)
text_adjective = visual.TextStim(win, pos=(0, -TEXT_DISTANCE), height=TEXT_SIZE, font='Geneva', bold=True)
clock = core.Clock()


"""
HANDY FUNCTIONS
"""

class csv_writer(object):
    def __init__(self, saveFilePrefix='', saveFolder=''):
        """
        Creates a csv file and appends single rows to it using the csvWriter.write() function.
        Use this function to save trials. Writing is very fast. Around a microsecond.

        :saveFilePrefix: a string to prefix the file with
        :saveFolder: (string/False) if False, uses same directory as the py file

        So you'd do this::
                # In the beginning of your script
                writer = ppc.csvWriter('subject 1', 'dataFolder')

                # In the trial-loop
                trial = {'condition': 'fun', 'answer': 'left', 'rt': 0.224}  # your trial
                writer.write(trial)
        """
        import csv, time

        # Create folder if it doesn't exist
        if saveFolder:
            import os
            saveFolder += '/'
            if not os.path.isdir(saveFolder):
                os.makedirs(saveFolder)

        # Generate self.saveFile and self.writer
        self.saveFile = saveFolder + str(saveFilePrefix) + ' (' + time.strftime('%Y-%m-%d %H-%M-%S', time.localtime()) +').csv'  # Filename for csv. E.g. "myFolder/subj1_cond2 (2013-12-28 09-53-04).csv"
        self.writer = csv.writer(open(self.saveFile, 'wb')).writerow  # The writer function to csv. It appends a single row to file
        self.headerWritten = False

    def write(self, trial):
        """:trial: a dictionary"""
        # Save to disk
        if not self.headerWritten:
            self.headerWritten = True
            self.writer(trial.keys())
        self.writer(trial.values())
writer = csv_writer(DIALOGUE['id'])  # initiate writer


# Translate order_id into list of condition-event translation
word_column_order = list(itertools.permutations(range(3)))[DIALOGUE['order_id']]  # selet a permutation of SELF, UPPERCASE, and OBAMA

# Load words
word_lists = pd.read_excel(DIALOGUE['words_file'])
word_lists = {
    'NULL': [''] * 1000,  # make plenty of NULLs at index 0
    'SELF': list(word_lists.ix[:,word_column_order[0]]),
    'UPPERCASE': list(word_lists.ix[:,word_column_order[1]]),
    'OBAMA': list(word_lists.ix[:,word_column_order[2]])
}

def make_trials(run_number):
    """ Returns a list of dictionaries, where each dictionary represents a trial """
    
    # Load sequence for this run number
    sequence_file = ORDER_FILES[run_number-1]
    sequence = pd.read_table(sequence_file, delim_whitespace=True, header=None, na_values=[], keep_default_na=False)
    judgement_types = sequence[4].replace(JUDGEMENT_MAP)  # pick the judgement type column and translate it
    durations = (sequence[2]/SCAN_TIME).astype(int)  # pick presentation time, convert from seconds (float) to scans (int)
    
    n_cases = sum(judgement_types == 'UPPERCASE')  # number of UPPERCASE trials
    n_cases_half = int(math.ceil(n_cases / 2.0))  # half that number used to generate...
    cases = ['LOWER']*n_cases_half + ['UPPER']*n_cases_half  # list of cases for UPPERCASE trials, half of each.
    random.shuffle(cases)  # random order
    
    # Loop through the list of trial order, then  fill out remaining info
    trials = []  # list of trials (dictionaries). Will be filled out below and then returned
    for trial_number, judgement_type in enumerate(judgement_types):
        case = cases.pop() if judgement_type == 'UPPERCASE' else 'UPPER'  # default to UPPER. Else pick from the list
        #case = cases[trial_number]
        adjective = word_lists[judgement_type].pop()
        
        trial = {            
            # Trial info
            'judgement': judgement_type,
            #'word_list': judgement_index,
            'adjective': adjective.upper() if case == 'UPPER' else adjective.lower(),# takes a word from this list and removes it
            'case': case,
            'duration': durations[trial_number],
            'trial_number': trial_number+1,  # start at 1 instead of 0
            'run_number': run_number,
            
            # Placeholders for answers
            'time_start': '',
            'answer': '',
            'rt': '',
        }
        trial.update(DIALOGUE)  # add data from dialogue (general session info)
        trials.append(trial)  # add this trial to the trial list
    
    
    
    
    return trials


def run_block(run_number):
    """ Takes a trial list and runs through it, displaying and recording appropriately """
    trials = make_trials(run_number)
    for trial in trials:
        # Prepare
        text_judgement.text = trial['judgement'] if trial['judgement'] != 'NULL' else ''
        text_adjective.text = trial['adjective']
        current_scan = 0  # number of TRs that this trial has been ongoing
        
        # Show trial
        fix.draw()
        text_judgement.draw()
        text_adjective.draw()
        win.flip()
        clock.reset()  # record reaction time from here
        trial['time_start'] = datetime.strftime(datetime.now(timezone('EST')), '%Y-%m-%dT%H:%M:%S.%fZ')  # get current absolute EST time with millisecond precision
        
        # Listen for response or scanner for the rest of the trial. 
        # This is a very thight loop. Runs probably more than 100000 times each second
        while True:
            # Collect response depending on setting. Scanner continues on trigger. Practice continues on time.
            if clock.getTime() > NONRESPONSE_WINDOW:
                if DIALOGUE['setting'] == 'SCANNER':
                    response = event.waitKeys(keyList=KEYS_SUBJECT.keys() + SCANNER_KEYS + QUIT_KEYS, timeStamped=clock, maxWait=SCAN_TIME*trial['duration'] - clock.getTime()+SCAN_TIME_BUFFER)
                    if response is None:
                        key = SCANNER_KEYS[0]
                    else:
                        key, rt = response[0]
                elif DIALOGUE['setting'] == 'PRACTICE':
                    response = event.waitKeys(keyList=KEYS_SUBJECT.keys() + QUIT_KEYS, timeStamped=clock, maxWait=SCAN_TIME*trial['duration'] - clock.getTime())
                    if response is None:
                        # Timeout, pretend that the scanner sent a trigger
                        key = SCANNER_KEYS[0]
                    else:
                        key, rt = response[0]
                # Record task responses
                if key in KEYS_SUBJECT.keys():
                    trial['answer'] = KEYS_SUBJECT[key]  # translate from key to meaning
                    trial['rt'] = rt              
                
                # Break out of while-loop if the scanner is beginning the next trigger
                if key in SCANNER_KEYS:
                    current_scan += 1  # a scan trigger was recorded
                    if current_scan >= trial['duration']:
                        break
                
                if key in QUIT_KEYS:
                    core.quit()

        # Save trial
        writer.write(trial)
        

def show_instruction(text):
    """Waits for the subject to continue; then waits for the next scanner
    trigger if this is in the scanner."""
    if DIALOGUE['setting'] == 'PRACTICE':  # only show instruction if there is a text to show
        text_judgement.text = text
        text_judgement.draw()
        win.flip()
        key = event.waitKeys(keyList=KEYS_SUBJECT.keys()+QUIT_KEYS)[0]  # just pick first response, no timestamp
        if key in QUIT_KEYS:
            core.quit()
    
    # Wait for scanner to start - 
    elif DIALOGUE['setting'] == 'SCANNER':
        win.flip()  # blank screen
        key = event.waitKeys(keyList=SCANNER_KEYS+QUIT_KEYS)[0]  # synchronize with scanner
        if key in QUIT_KEYS:
            core.quit()

"""
EXECUTE EXPERIMENT
"""

# Run experiment with break. Start at specified start_run
if DIALOGUE['start_run'] == 1:
    # Show instructions
    show_instruction(INSTRUCTIONS[DIALOGUE['setting']])  # Translate from setting to instruction text
    run_block(1)
if DIALOGUE['start_run'] <= 2:
    show_instruction(INSTRUCTIONS['break'])
    run_block(2)
if DIALOGUE['start_run'] <= 3:
    show_instruction(INSTRUCTIONS['break'])
    run_block(3)

# Finished, yay!