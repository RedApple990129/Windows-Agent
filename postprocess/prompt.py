CLICK_ACTION_DESCRIPTION_PROMPT = """Help me describe the target in the screenshot. The target may be a GUI element or an empty area on the screen.

You will be provided with:
1. A screenshot with a red mark quadruplet:
   - Frame: rectangular border around the target (may be inaccurate)
   - Circle: circle at the center of the target
   - Point: dot marking the exact click position
   - Arrow: pointing to the target
2. The name of the clicked target for reference. It's just for reference. If this name is "Unknown" or appears to be incorrect, just ignore it.

Description Rules:
1. Priority Order:
   - Highest: Circle, Point and Arrow
   - Second: Reference name (if reliable)
   - Lowest: Frame

2. Description Strategy:
   A. For Clear GUI Elements:
      - Include position info ("top", "left", "center", etc.) if possible
      - Use visual information to describe the element
      - Refer to the provided element name if reliable
      - Examples:
        √ "the button in the top-right corner of the window"
        √ "the current tab at the top of the browser"
        x "the red circle" (red marks doesn't belong to the original screenshot or element)
   
   B. For Empty Areas or Uncertain Elements:
      - Focus on positional relationships
      - Use visual information to locate the position
      - Examples:
        √ "empty area on the right side of the window"
        √ "area near the bottom toolbar"

3. Prohibited:
   - No speculation about element functions
   - No uncertain terms like "seems", "appears", "probably"
   - No description of elements outside the frame

Output Format:
- For GUI elements: "{position description} + {element description}"
- For empty areas: "empty area + {position description}"

Examples:
√ "the close button in the top-right corner of the window"
√ "the 'Chrome' icon on the desktop"
√ "the left thumbnail panel in current window"
√ "the 'Images' tab below the search bar"
√ "'click to add title'"
√ "the button in the top-right corner of the browser" (when the reference name is not reliable and you are unsure about the element)
x "what appears to be a settings button" (avoid speculation)

Important:
1. Carefully observe the screenshot and the red mark quadruplet. Use these visual cues to describe the element or position as accurately as possible. But **DO NOT** explicitly state the red marks in your description. Avoid phrases like "red arrow marking on the slide.." or "the red circle.." 
2. When uncertain, prefer positional description over semantic or functional speculation. Be extraordinarily cautious to avoid hallucinations.
3. Be precise and output the description directly in an objective tone. Avoid sentences starting with "the target is","The pointed target is", or "it appears to be".
4. Do not directly use the provided element name, create your own natural description based on visual information.

Note:
1. For the name of the clicked target for reference, it is either very precise or completely worthless. Judge its reliability based on visual information.
If unreliable, ignore it and be cautious, preferably using only positional descriptions; if reliable, try to expand on its description as much as possible.

2. Special cases: for the text box in PowerPoint, the name of the clicked target is usually "click to add title" or "click to add text".
- "'click to add title'": for the title text box above the content text box or on the cover slide
- "'click to add text'": for the content text box below the title text box
- "'click to add subtitle'": for the subtitle text box below the title text box
- "'the left thumbnail panel in current window'": for the **left slides thumbnail panel in PowerPoint**. But **DO NOT** abuse the use of "thumbnail" in other cases.
"""

CLICK_ACTION_DESCRIPTION_CHECK_PROMPT = """
You are provided with the following information about a mouse click on a computer screen:

1. A screenshot showing:
   - A red dot and circle marking the exact click location
   - A red arrow pointing to the click location
   - A red box outlining the general area of the clicked element
   Note: While the dot, circle, and arrow are precise, the box might be less accurate

2. The exact coordinates of the mouse click

3. The element name from the accessibility tree
   Note: This information might be incomplete, with many elements labeled as "unknown".

4. A pre-generated description of the click location
   Types:
   - Empty area description (e.g., "empty area near the bottom toolbar")
   - Specific element description (e.g., "the start button on the left corner of the taskbar")

# Your Task
Evaluate the provided description, determine if it is accurate. If not, provide the correct description. You can describe it as an empty area or a specific element. Do not mention the red marks on the screenshot.

# Critical Evaluation Points
1. **Priority of Visual Evidence**: The red markers (dot, circle, arrow) on the screenshot show the ACTUAL click location. This is your primary source of truth. But **DO NOT** explicitly state the red marks in your description. Avoid phrases like "red arrow marking on the slide.." or "the red circle.." 

2. **Element Name Usage**:
   - Ignore if marked as "unknown"
   - If available, use it to verify the description's accuracy
   - If there's a conflict between the element name and the description, carefully evaluate which is correct

3. **Empty Area vs. Specific Element Distinction**:
   - True empty areas: Locations where clicks produce no effect
   - False empty areas: Locations that appear empty but are part of specific functional elements

# Evaluation Process
1. First, locate the exact click point using the red markers
2. Check if the provided element name offers any useful information
3. Determine if the location is a true empty area or part of a specific functional element
4. Compare the given description against your findings
5. Provide your response based on the required format

# Important
- Carefully determine the wrong description. Most of the time, the provided description is correct.
- The pre-generated description may have hallucinations. Carefully evaluate it.

Final Answer Format:(Response in English even the element name is Chinese)
Thought Process: {your thought process}
Answer:{your answer}

Your answer should be either:
- "Good" if the description is accurate
- "Wrong. Correct Description: {your description}" if the description is inaccurate
--------------------------------------------

"""


THOUGHT_PROMPT = """You are a helpful PC Agent designed to complete tasks on a computer. Your goal is to recreate your **thought process** behind a specific action.

You will be provided with:

1. The task you are attempting to complete.
2. A history of the steps you have already performed (up to 50, if any; none if it was the first action).
3. Subsequent actions (none if this is the last action).
4. The specific action you chose to take.
5. A screenshot of the computer screen at the moment you decided to take the action
6. The red marks on the screenshot:
   A. For Click Actions (click, right click, double click):
    - Frame: rectangular border around clicked element
    - Center: circle at element center
    - Click: point at exact click position
    - Arrow: pointing to clicked element
   B. For Drag Actions:
    - Start: red point and circle
    - End: red point and circle  
    - Arrow: from start to end position

Explanation of actions:
1. **click element: <{element description}>**: Click the element described by `{element description}`.
2. **right click element: <{element description}>**: Right-click the element described by `{element description}`.
3. **double click element: <{element description}>**: Double-click the element described by `{element description}`.
4. **drag from (x1, y1) to (x2, y2)**: Drag the mouse from the position (x1, y1) to (x2, y2).
5. **scroll (dx, dy)**: Scroll with offsets (dx for horizontal movement, dy for vertical movement).
6. **press key: key_content**: Press the `key_content` on the keyboard.
7. **hotkey (key1, key2)**: Press the combination of `key1` and `key2`.
8. **type text: text_content**: Type the text `text_content` on the keyboard.
9. **wait**: Pause briefly, usually for system responses or screen updates.
10. **finish**: Indicate the task has been completed.
11. **fail**: Indicate the task has failed.

Further explanation of drag operation: drag from (x1, y1) to (x2, y2) is a combination of press the mouse at (x1, y1) and drag it to (x2, y2). It might has following purposes:
1. Move/Translate - Moving an element from position (x1,y1) to (x2,y2)
Common scenarios:
- Dragging a file/folder to a new location
- Moving a UI element (window, widget) to a different position
- Moving elements (shapes, text boxes, images) in a PowerPoint slide
- Adjusting slider controls or resizing elements
- Reordering items in a list or menu

2. Range Selection - Selecting content within a rectangular region defined by (x1,y1) and (x2,y2) as diagonal points
Common scenarios:
- Selecting multiple files/icons in a folder
- Selecting text in a document. This is usually performed before copy/cut/delete/adjust text operation. After this action, the selected text will be highlighted.
- Selecting cells in a spreadsheet
- Drawing selection rectangle on a canvas

Consider the following to give your thought process:
1. The current state of the screen and your last step (if any). Does current state align with your last plan? Are this action trying to fix something?
2. Based on the history steps, how far have you progressed in the whole task? And based on your subsequent actions, what is the expected outcome of this action? (**DO NOT** explicitly state the next action in your output.)
3. Based on all the information (task, observation, history, future), if this action seems not related to the task, is it possibly exploring the environment?
Based on the above, recreate your thought process in a clear, natural first-person narrative.

Other requirements:
1. Be confident in your thought process. Avoid speculative or uncertain phrases like "it seems" or "this action might have been for."
2. You may reference future actions as context, but **DO NOT** explicitly state the next action in your explanation.
3. If there are red marks on the screenshot, you should use them to understand the action, but **DO NOT** explicitly state the red marks in your explanation. Avoid phrases like "I notice the red circles around..." or "the red arrow indicates...".
3. Keep your explanations **concise and short**, do not conduct meaningless analysis and emphasis.
4. Do not repeat the action after your thought process.

Here are some examples of the thought process:
- "I see the 'View' menu is successfully opened, so I can click the 'Slide Master' button on it to change the font for all slides."
- "To open the target powerpoint file, I should open the folder containing it first. So I need to click the folder icon on the left of the taskbar."
- "I want to click the close button to close the current window in my last step, but I see it is not closed yet in current screen. Maybe my click was not precise last time, so I need to click it again. I should click the close button on the right top corner of the window."
- "After save the file to desktop, I have successfully completed the task."
- "I need to modify the 5th slide, but it is not in the current screen. I should scroll down the page to find it."
- "I have insert a new text box and focus on it, so I can type the content now."
- "I have finished typing content in the text box. Now I can click anywhere outside the text box to deselect it and view the content on the slide."
- "I see the current file name is 'Untitled', so I should change it to a proper name. First I need to click the text box of the file name to focus on it."
- "I need to insert a new slide, so I can first click the left thumbnail panel in the PowerPoint window."
- "I need to insert a new slide, and I have clicked the left thumbnail panel in the PowerPoint window. Now I need to press key enter to insert a new slide."

Examples of thought processes for exploratory actions:
- "I need to save the file to the desktop, but I don't see a desktop option in the window. Maybe I should scroll down to see if there's a desktop option."
- "I want to select the save button, but I don't see a save option in the window. I guess I might find it by clicking the File button."
- "I need to open the settings menu, but I don't see an obvious settings icon on the current interface. Perhaps I should click on the three dots or three horizontal lines icon in the top right corner, as these often hide more options."
- "I want to change the document's font, but I can't find the font option on the toolbar. I might need to click on the 'Format' or 'Style' menu to see if I can find the font settings there."
- "I need to insert an image, but I don't see an obvious 'Insert' button. I guess I might need to right-click on a blank area of the document to see if there's an option to insert an image in the context menu."
- "I want to check the version information of this application, but I can't find the relevant option on the main interface. Maybe I should click on the 'Help' or 'About' menu, as version information is often found there."
- "I need to exit this full-screen program, but I don't see an exit button. I can try pressing the ESC key or moving the mouse to the top of the screen to see if a hidden menu bar appears."
- "I want to search for specific content on this webpage, but I don't see a search box. I can try using the shortcut Ctrl+F (or Command+F) to see if it brings up the in-page search function."

Additional PowerPoint Operation Tip:
- These steps are to add a new slide at the end of the presentation:
  1. Click in the left thumbnail panel of the PowerPoint window.
  2. Press the Enter key to insert a new slide.
- These steps are to add text in the text box:
  1. Click 'click to add text'/'click to add title'/'click to add subtitle' to focus on the text box.
  2. Type the content in the text box.
  3. (Optional) Press the Enter key to finish.

Again, you are recreating your thought process when you made the action, so you should not include any post-event evaluation or similar phrases.

--------------------------------------------

"""











