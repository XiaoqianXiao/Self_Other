# Self_Other
# Work on psychopy v2024.1.5
original number of trials:
run1: 134
run2: 137
run3: 134
Change:
get rid of 16 items in run3 (4 for each condition), then put: 
1) 13 * 3 conditions from run3 to run1 and run2
2) 21 NULL from run3 to run1
3) 18 NULL from run3 to run2
   
end up with 194 trials/run in 2 runs in total

the total time for each run will be 600s + reaction time of last trial/ 600s + longest wait time for last trial.

Add fixation time before the target and after the response.


###
# Things keep in mind:
1. The scripts do not have function for recording results if exiting in the middle of the test. Which could happen during scan.
2. Keep the stimuli on the screen could increase the affection of the former trial. Hide the stimuli after response is suggested.
3. There was no instruction for scan version
