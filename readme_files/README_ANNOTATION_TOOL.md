# The *Suzipu* Musical Annotation Tool

Purpose: The *Suzipu* Musical Annotation Tool is used for the creation of digital representations of *suzipu*
notation. Given a collection of images containing *suzipu* notation, it provides everything needed to annotate
the images with segmentation boxes and notation information. This is the ideal tool for creating datasets for
use in OMR (optical music recognition) settings.

## Tutorial

In this short tutorial, the goal is to annotate Jiang Kui's piece *Geximeiling* 鬲溪梅令 from the collection
*Baishidaoren Gequ* 白石道人歌曲. All the necessary image material is found in the folder `tutorial`, and the
file `tutorial/01_geximeiling.json` is the result of this tutorial.

## Table of Contents
0. [Preparing the Environment](#preparing-the-environment)
1. [Choosing the Correct Paths](#choosing-the-correct-paths)
2. [Creating Segmentation Boxes](#creating-segmentation-boxes)
3. [Marking Segmentation Boxes](#marking-segmentation-boxes)
4. [Annotating Text](#annotating-text)
5. [Annotating *Suzipu*](#annotating-suzipu)
6. [Mode Information](#mode-information)
7. [Statistical Information](#statistical-information)
8. [Notational Information](#notational-information)
9. [Export Functions](#export-functions)
10. [Extract OMR Dataset from Corpus](#extract-omr-dataset-from-corpus)

### Preparing the Environment

1. Make sure that `Python 3.10` is installed with the `tkinter` library. Under Windows `tkinter` should be
provided by default. See also: [Ubuntu install](https://www.pythonguis.com/installation/install-tkinter-linux/),
[MacOS install](https://www.pythonguis.com/installation/install-tkinter-mac/).
2. Install the requirements from [requirements.txt](requirements.txt) using `pip`. This may be platform dependent, e.g.,
   under Ubuntu this can be achieved with the command `python3 -m pip install -r requirements.txt`.
3. In order to use the annotation tool, the segmentation algorithm's weight file `HRCenterNet.pth.tar` must
   be downloaded:
   [See the links provided in HRCenterNet's README](https://github.com/Tverous/HRCenterNet#download-the-dataset-and-the-pretrained-weight).
4. Furthermore, the downloaded weight file `HRCenterNet.pth.tar` must be moved to the folder `weights` in the repository's
   root folder.
5. For using the text-based `Intelligent Fill...` function, the file `chi_tra.traineddata` for `tesseract` must be
   present in the folder `weights` in the repository's root folder. For best results, use Wang Dingyun's trained model
   from [this site](https://github.com/gumblex/tessdata_chi/releases/tag/v20220621).


For starting the annotation tool, follow these steps:
1. Change the console directory to the root of the git repository.
2. Start the annotation tool by executing the file `annotation_editor.py`. This is usually done using one
   of these commands: `python3 annotation_editor.py` or `python annotation_editor`.

The package is tested under Ubuntu only. Windows and MacOS have not been tested yet. If something doesn't
work, please open an issue in GitHub.

### Choosing the Correct Paths

<img src="annotation_tool_tutorial/1.png" width="400">

First, the correct paths must be chosen. In this tutorial, we are going to use the path `./tutorial` in the
project root directory for both the image directory and the output directory, where everything needed for the tutorial
is already present. Click on `Continue`.

### Creating Segmentation Boxes

<img src="annotation_tool_tutorial/2.png" width="400">

Three windows opened, the `Main Window`, `the Canvas Window` and the `Additional Info Window`.
First, take a look at the `Canvas Window`. We see that on this page, only the last two columns belong to
*Geximeiling* 鬲溪梅令.

<img src="annotation_tool_tutorial/3.png" width="400">

Now, take a look at the upper part of the `Main Window`. Using the `+` button marked in red, we set the
number of pages to $2$.

<img src="annotation_tool_tutorial/4.png" width="400">

This caused the second page to appear in the `Canvas Window`. With the mouse wheel and the left mouse button, the
image can be scaled and the displayed area can be moved.

<img src="annotation_tool_tutorial/5.png" width="400">

Using the button `New Segmentation` in the `Main Window`, ...

<img src="annotation_tool_tutorial/6.png" width="400">

... the segmentation algorithm created a preliminary segmentation of the piece. Many boxes on the right and left do not
belong to *Geximeiling* 鬲溪梅令, and some boxes are drawn incorrectly.

<img src="annotation_tool_tutorial/7.png" width="400">

Therefore, select `Delete` in the `Main Window`.

<img src="annotation_tool_tutorial/8.png" width="400">

In the mode `Delete`, boxes are deleted by hovering over them while clicking the right mouse button. Firstly,
delete all boxes not belonging to *Geximeiling* 鬲溪梅令.

<img src="annotation_tool_tutorial/9.png" width="400">

Secondly, check the remaining boxes whether they fit the characters well. If not, these are also deleted with the right
mouse button. In the next step, we are going to redraw them manually.

<img src="annotation_tool_tutorial/10.png" width="400">

In the `Main Window`, choose the button `Create`.

<img src="annotation_tool_tutorial/11.png" width="400">

In the mode `Create`, create new boxes the following way: First, move the mouse cursor to the upper left corner
of the place where the segmentation box should appear. Hold down the right mouse button and move it to the place where
its lower right corner should be. When releasing the right mouse button, the new segmentation box appears.

### Marking Segmentation Boxes

<img src="annotation_tool_tutorial/12.png" width="400">

In the `Main Window`, choose the button `Mark`, and choose the type label button `Title`.

<img src="annotation_tool_tutorial/13.png" width="400">

In the mode `Mark`, we can change the boxes' labels by hovering over them while the right mouse button is
pressed. Since the type `Title` is selected, the marked boxes take on a blue color.

<img src="annotation_tool_tutorial/14.png" width="400">

Repeating this with all the other type labels, every box in the piece is marked correctly. No boxes of type
`Unmarked` should be present anymore.

<img src="annotation_tool_tutorial/15.png" width="400">

In order to represent the blanks dividing the piece into two stanzas, create empty boxes around the spaces.

<img src="annotation_tool_tutorial/16.png" width="400">

After deleting, creating or marking segmentation boxes, the correct reading order for the later annotation step has to
be ensured. This is done using the button `Infer Box Order and Column Breaks`. If this is not done, the
tool will randomly jump between the boxes in the `Annotation` mode.

### Annotating Text

<img src="annotation_tool_tutorial/17.png" width="400">

In the `Main Window`, choose the mode `Annotation`. Firstly, choose the type label button `Title`.
The `Text Annotation` textbox is now ready to be filled with the correct character.

<img src="annotation_tool_tutorial/18.png">

Fill in the character "鬲".

<img src="annotation_tool_tutorial/18_2.png" width="400">

Using the buttons `<< Previous` and `Next >>`, all four title characters are easily annotated. In
addition, using the right click in the `Canvas Window`, a box can be selected. The currently selected box is
marked with a thicker border in the `Canvas Window`.

<img src="annotation_tool_tutorial/19.png" width="400">

Annotating each box one after one is a tiresome process. Now, we annotate the preface by selecting the type
`Preface`. Instead of annotating each of the 11 boxes manually, use the quick fill function.

<img src="annotation_tool_tutorial/20.png">

In the quick fill textbox, paste the string "丙辰冬自無錫歸作此寓意". Then, annotate the mode and lyrics.

### Annotating *Suzipu*

<img src="annotation_tool_tutorial/21.png" width="400">

When the mode `Annotation` with type `Music` is selected, the `Suzipu Annotation` is enabled.
Similar to before, annotate each box by choosing the correct notational symbols. Here, the first *suzipu* character is
already a pair-character notation, so the first and second symbols must be assigned accordingly.

<img src="annotation_tool_tutorial/22.png" width="400">

When annotating the 19th *suzipu* character, assume that the upper part of this pair-character notation
is not *Gou* ![](../res/suzipu_notation/gou.png), but instead a misprint of *He* ![](../res/suzipu_notation/he.png).
Annotate as such, and exclude the box from the
image dataset by marking the checkbox marked in red.

<img src="annotation_tool_tutorial/22_2.png">

Also for *suzipu* notation, quick fill can be used. Each cell is separated using the vertical bar character 
|", and the contents of each cell are up to two characters as explained in the paper.

### Mode Information

<img src="annotation_tool_tutorial/23.png" width="400">

Now, have a closer look on the left side of the `Additional Info Window`. The selection box marked in red
currently contains no mode. Since we already have annotated the `Title` information of the piece indicating
*Xianlüdiao* 仙吕调, we can quickly infer the mode by clicking the button `Infer Mode from Segmentation Boxes` marked
in blue. Alternatively, we can directly click on the mode selector, ...

<img src="annotation_tool_tutorial/24.png">

... and choose the mode from the list, ...

<img src="annotation_tool_tutorial/25.png" width="400">

... or click on the `Custom Mode Picker` button to create a custom mode, ...

<img src="annotation_tool_tutorial/26.png">

... so we have the possibility to choose from all 84 modes, instead of the 30 modes in the list, by choosing one out of
12 *lülü* corresponding to *Gong* 宫, and one out of the 7 final notes.

### Statistical Information

<img src="annotation_tool_tutorial/27.png" width="400">

Below, the `Statistics` field displays the absolute occurrence of each pitch and secondary *suzipu* character.

### Notational Information

<img src="annotation_tool_tutorial/28.png" width="400">

On the right side, the `Modern Notation` field displays an on-the-fly rendered score of the piece, where the
structure follows the original score as closely as possible. The pitch characters are transformed into modern
*jianpu* 简谱 notation, and *He* ![](../res/suzipu_notation/he.png) is rendered as **•1**
by default. The secondary symbols are rendered above the notes with the first character of their name, except for
*Dadun* 大顿, *Xiaozhu* 小住 and *Dazhu* 大住, which are rendered using their *suzipu* glyphs as
![](../res/suzipu_notation/add_dadun.png), ![](../res/suzipu_notation/add_xiaozhu.png), and
![](../res/suzipu_notation/add_dazhu.png) respectively.

<img src="annotation_tool_tutorial/29.png" width="400">

Using the dropdown menu marked in red, another fingering can be used, e.g., such that *He*
![](../res/suzipu_notation/he.png) is rendered as **•6**.

<img src="annotation_tool_tutorial/30.png" width="400">

When clicking at the five-line notation button, the score is on-the-fly rendered to appear as five-line notation.

<img src="annotation_tool_tutorial/31.png" width="400">

### Export Functions

Using the button `Export Notation as Image`, ....

<img src="annotation_tool_tutorial/32.png" width="400">

... the notation image is saved as a PNG file, including the title, the mode as stated in the mode segmentation boxes,
in parentheses the mode as selected in the mode selection menu, and the preface.

<img src="annotation_tool_tutorial/32_2.png" width="400">

With the button `Export Notation as MusicXML`, ...

<img src="annotation_tool_tutorial/32_3.png" width="400">

... the transnotation into modern five-line notation is saved in MusicXML representation, and can then be processed by
other software. The image file shown here was generated using MuseScore, a program which can be used to view or modify
MusicXML files, and also allows for playback of the melody.

<img src="annotation_tool_tutorial/33.png" width="400">

When clicking on the button `Export as Text`, ...

<img src="annotation_tool_tutorial/34.png" width="400">

... a textual representation of the piece is saved as a TXT file, again including the title, the mode as given in the
original piece, the user-selected mode in parentheses, the lyrics, and the music in the same format as applicable in the
music `Quick Fill` function.

### Extract OMR Dataset from Corpus

In order to extract an OMR dataset from the corpus, the file `extract_dataset_from_corpus.py` must be used. It is in the
repository's root folder, and should be executed using the following syntax:

```
usage: extract_dataset_from_corpus.py [-h] --corpus_dir CORPUS_DIR --output_dir
                                      OUTPUT_DIR

Suzipu Annotated OMR Dataset Export Script.

options:
  -h, --help            show this help message and exit
  --corpus_dir CORPUS_DIR
                        Path to the folder which contains the corpus files (JSON
                        format). The folder is checked recursively for any JSON
                        files placed inside this folder or subfolders.
  --output_dir OUTPUT_DIR
                        Path to the output folder to which the dataset is saved. If
                        it doesn't exist, the script will try to create the folder.
```

In our example, let's try to execute it with the corpus directory `--corpus_dir ./tutorial` and the output directory
`--output_dir ./omr_dataset`. The folder `omr_dataset` is created, and the contents are two subfolders:

<img src="export_omr_dataset_tutorial/01.png">

In folder `Music`, the image data associated with notation boxes is saved, while  folder `Text` contains the text-based
image data (i.e., title, mode, preface or lyrics) is saved.

<img src="export_omr_dataset_tutorial/02.png">

In each folder is a folder `images` and a `dataset.json`, ...

<img src="export_omr_dataset_tutorial/03.png">

... which is a list of all files in this subfolder, with the file names indexed in field `file_name`, the original
segmentation box type stored in field `type`, and the annotation string contained in field `annotation`.

<img src="export_omr_dataset_tutorial/04.png">

In the subfolder `images`, the extracted images are contained.
