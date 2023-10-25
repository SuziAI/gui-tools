# The *Suzipu* Musical Annotation Tool

Purpose: The *Suzipu* Musical Annotation Tool is used for the creation of digital representations of *suzipu*
notation. Given a collection of images containing *suzipu* notation, it provides everything needed to annotate
the images with segmentation boxes and notation information. This is the ideal tool for creating datasets for
use in OMR (optical music recognition) settings.

## Tutorial

In this short tutorial, the goal is to annotate Jiang Kui's piece *Geximeiling* 鬲溪梅令 from the collection
*Baishidaoren Gequ* 白石道人歌曲. All the necessary image material is found in the folder `tutorial`, and the
file `tutorial/01_geximeiling.json` is the result of this tutorial.

### Choosing the Correct Paths

<img src="annotation_tool_tutorial/1.png" width="200">

First, the correct paths must be chosen. In this tutorial, we are going to use the path `./tutorial` in the
project root directory for both the image directory and the output directory, where everything needed for the tutorial
is already present. Click on `Continue`.

### Creating the Segmentation Boxes

![](annotation_tool_tutorial/2.png)

Three windows opened, the `Main Window`, `the Canvas Window` and the `Additional Info Window`.
First, take a look at the `Canvas Window`. We see that on this page, only the last two columns belong to
*Geximeiling* 鬲溪梅令.

![](annotation_tool_tutorial/3.png)

Now, take a look at the upper part of the `Main Window`. Using the `+` button marked in red, we set the
number of pages to $2$.

![](annotation_tool_tutorial/4.png)

This caused the second page to appear in the `Canvas Window`. With the mouse wheel and the left mouse button, the
image can be scaled and the displayed area can be moved.

![](annotation_tool_tutorial/5.png)

Using the button `New Segmentation` in the `Main Window`, ...

![](annotation_tool_tutorial/6.png)

... the segmentation algorithm created a preliminary segmentation of the piece. Many boxes on the right and left do not
belong to *Geximeiling* 鬲溪梅令, and some boxes are drawn incorrectly.

![](annotation_tool_tutorial/7.png)

Therefore, select `Delete` in the `Main Window`.

![](annotation_tool_tutorial/8.png)

In the mode `Delete`, boxes are deleted by hovering over them while clicking the right mouse button. Firstly,
delete all boxes not belonging to *Geximeiling* 鬲溪梅令.

![](annotation_tool_tutorial/9.png)

Secondly, check the remaining boxes whether they fit the characters well. If not, these are also deleted with the right
mouse button. In the next step, we are going to redraw them manually.

![](annotation_tool_tutorial/10.png)

In the `Main Window`, choose the button `Create`.

![](annotation_tool_tutorial/11.png)

In the mode `Create`, create new boxes the following way: First, move the mouse cursor to the upper left corner
of the place where the segmentation box should appear. Hold down the right mouse button and move it to the place where
its lower right corner should be. When releasing the right mouse button, the new segmentation box appears.

### Marking the Segmentation Boxes

![](annotation_tool_tutorial/12.png)

In the `Main Window`, choose the button `Mark`, and choose the type label button `Title`.

![](annotation_tool_tutorial/13.png)

In the mode `Mark`, we can change the boxes' labels by hovering over them while the right mouse button is
pressed. Since the type `Title` is selected, the marked boxes take on a blue color.

![](annotation_tool_tutorial/14.png)

Repeating this with all the other type labels, every box in the piece is marked correctly. No boxes of type
`Unmarked` should be present anymore.

![](annotation_tool_tutorial/15.png)

In order to represent the blanks dividing the piece into two stanzas, create empty boxes around the spaces.

![](annotation_tool_tutorial/16.png)

After deleting, creating or marking segmentation boxes, the correct reading order for the later annotation step has to
be ensured. This is done using the button `Infer Box Order and Column Breaks`. If this is not done, the
\annotationtool will randomly jump between the boxes in the `Annotation` mode.

### Annotating Text

![](annotation_tool_tutorial/17.png)

In the `Main Window`, choose the mode `Annotation`. Firstly, choose the type label button `Title`.
The `Text Annotation` textbox is now ready to be filled with the correct character.

![](annotation_tool_tutorial/18.png)

Fill in the character "鬲".

![](annotation_tool_tutorial/18_2.png)

Using the buttons `<< Previous` and `Next >>`, all four title characters are easily annotated. In
addition, using the right click in the `Canvas Window`, a box can be selected. The currently selected box is
marked with a thicker border in the `Canvas Window`.

![](annotation_tool_tutorial/19.png)

Annotating each box one after one is a tiresome process. Now, we annotate the preface by selecting the type
`Preface`. Instead of annotating each of the 11 boxes manually, use the quick fill function.

![](annotation_tool_tutorial/20.png)

In the quick fill textbox, paste the string "丙辰冬自無錫歸作此寓意". Then, annotate the mode and lyrics.

### Annotating *Suzipu*`

![](annotation_tool_tutorial/21.png)

When the mode `Annotation` with type `Music` is selected, the `Suzipu Annotation` is enabled.
Similar to before, annotate each box by choosing the correct notational symbols. Here, the first *suzipu* character is
already a pair-character notation, so the first and second symbols must be assigned accordingly.

![](annotation_tool_tutorial/22.png)

When annotating the 19th *suzipu* character, assume that the upper part of this pair-character notation
is not *Gou* ![](../res/suzipu_notation/gou.png), but instead a misprint of *He* ![](../res/suzipu_notation/he.png).
Annotate as such, and exclude the box from the
image dataset by marking the checkbox marked in red.

![](annotation_tool_tutorial/22_2.png)

Also for *suzipu* notation, quick fill can be used. Each cell is separated using the vertical bar character 
|", and the contents of each cell are up to two characters as explained in the paper.

### Mode Information

![](annotation_tool_tutorial/23.png)

Now, have a closer look on the left side of the `Additional Info Window`. The selection box marked in red
currently contains no mode. Since we already have annotated the `Title` information of the piece indicating
*Xianlüdiao* 仙吕调, we can quickly infer the mode by clicking the button `Infer Mode from Segmentation Boxes` marked
in blue. Alternatively, we can directly click on the mode selector, ...

![](annotation_tool_tutorial/24.png)

... and choose the mode from the list, ...

![](annotation_tool_tutorial/25.png)
... or click on the `Custom Mode Picker` button to create a custom mode, ...

![](annotation_tool_tutorial/26.png)

... so we have the possibility to choose from all 84 modes, instead of the 30 modes in the list, by choosing one out of
12 \lvlv corresponding to \Gong, and one out of the 7 final notes.

### Statistical Information

![](annotation_tool_tutorial/27.png)

Below, the `Statistics` field displays the absolute occurrence of each pitch and secondary *suzipu* character.

### Notational Information

![](annotation_tool_tutorial/28.png)

On the right side, the `Modern Notation` field displays an on-the-fly rendered score of the piece, where the
structure follows the original score as closely as possible. The pitch characters are transformed into modern
*jianpu* 简谱 notation, and *He* ![](../res/suzipu_notation/he.png) is rendered as **•1**
by default. The secondary symbols are rendered above the notes with the first character of their name, except for
*Dadun* 大顿, *Xiaozhu* 小住 and *Dazhu* 大住, which are rendered using their *suzipu* glyphs as
![](../res/suzipu_notation/add_dadun.png), ![](../res/suzipu_notation/add_xiaozhu.png), and
![](../res/suzipu_notation/add_dazhu.png) respectively.

![](annotation_tool_tutorial/29.png)

Using the dropdown menu marked in red, another fingering can be used, e.g., such that *He*
![](../res/suzipu_notation/he.png) is rendered as **•6**.

![](annotation_tool_tutorial/30.png)

When clicking at the five-line notation button, the score is on-the-fly rendered to appear as five-line notation.

![](annotation_tool_tutorial/31.png)

Using the button `Export Notation as Image`, ....

![](annotation_tool_tutorial/32.png)

... the notation image is saved as a PNG file, including the title, the mode as stated in the mode segmentation boxes,
in parentheses the mode as selected in the mode selection menu, and the preface.

![](annotation_tool_tutorial/32_2.png)

With the button `Export Notation as MusicXML`, ...

![](annotation_tool_tutorial/32_3.png)

... the transnotation into modern five-line notation is saved in MusicXML representation, and can then be processed by
other software. The image file shown here was generated using MuseScore, a program which can be used to view or modify
MusicXML files, and also allows for playback of the melody.

![](annotation_tool_tutorial/33.png)

When clicking on the button `Export as Text`, ...

![](annotation_tool_tutorial/34.png)

... a textual representation of the piece is saved as a TXT file, again including the title, the mode as given in the
original piece, the user-selected mode in parentheses, the lyrics, and the music in the same format as applicable in the
music `Quick Fill` function.

