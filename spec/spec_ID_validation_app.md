The goal is to create a web interface for validating the action (velocity and heading_angle/steering) trajectory generated from "data/cosmos3/run_inverse_dynamics.py" manually.

# Graphical Interface:
- The interface shows the video on the left and the real-time plot of the corresponding action trajectory on the right
- The user can specify a folder in "data/datasets/generated_vids" from where the videos should be read from. Only videos in the specified folder are read in that session.
- The user walks through the videos with a Next/Previous button
- Each video has a corresponding text file with the same stem name but extension ".txt". By defult this is the text file from which the action trajectory for the velocity and heading_angle is read from. The user can choose to read the "Full FPS" version instead. The 'Full FPS' version has "_10fps" appended to the stem name. The text file with the same stem name as the video is the "Downsampled" version.
- The Full FPS version is sampled at 10Hz, the Downsampled version is downsampled to 5Hz. The real-time plot should be in sync with the video when a pair (video and trajectory) is played.
- The user should also be able to choose whether they want to see the velocity trajectory or the heading_angle angle trajectory in the real-time plot on the right. Only one should be plotted at a time.
- The text file sequence format is [[velocity, heading_angle_from_center], ...]. The velocity is in mph and the heading angle is in deg
- At the buttom there should be two buttons where the user manually marks the pair as Valid or Invalid.
- Below the buttons, there should be a field to enter comments which can be saved as part of the results below.

### Action:
- We need to extract the action sentence (the second to the last sentence of the matching prompt line) as done in the inverse dynamics script (data/cosmos3/run_inverse_dynamics.py) for the heuristic verification:
> 4. validates the tail of the native-rate sequence against the last sentence of
     the matching prompt line. The video tree under generated_vids mirrors the
     prompts tree (default data/cosmos3/video_gen_prompts, override with
     --prompts-root or PROMPTS_ROOT): for each video the nearest
     updated_human_prompt.txt (falling back to prompt.txt) is found by walking
     up the mirrored directory path, with '<name>_variants' folders sharing
     '<name>'s prompt file. prompt_N (variant suffixes like prompt_3_v07 are
     trimmed) maps to line N (0-based) of that file; mismatches are flagged.

- Read the script to understand the mechanism for extracting the action sentence.
- At the top of the window, print the extracted action sentence, so the user knows what the vehicle ought to doing


### Heuristic Label:
- The inverse dynamics script already tries to use a heuristic to validated the generated action trajectory
- The result of the heuristic validation is in "data/datasets/generated_vids/inverse_dynamics_flags.txt"
- If the heuristic validation flags the current video (the filepath is flagged in data/datasets/generated_vids/inverse_dynamics_flags.txt), add a note indicating this below the action sentence above


### Others:
- The user should be able to pause, replay, etc. the video in the player
- The user should have the option to disable real-time plotting of the trajectory, in which case the trajectory is plotted in full immediately.


# Result:
- The results are to be tracked and updated in a csv file "data/cosmos3/data_validation/inverse_dynamics_filter.csv"
- The CSV has the following columns: Video filepath relative to "data/datasets/generated_vids"; Valid/Invalid; Heuristic Validation; Comment
- The CSV should be updated as the user presses the Valid/Invaliid button in the interface