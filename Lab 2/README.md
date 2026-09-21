# Interactive Prototyping: The Clock of Pi
**NAMES OF COLLABORATORS HERE**
Hong Yuan Cao (hc2343), Yun-Chung Liu (yl4445)

Does it feel like time is moving strangely during this semester?

For our first Pi project, we will pay homage to the [timekeeping devices of old](https://en.wikipedia.org/wiki/History_of_timekeeping_devices) by making simple clocks.

It is worth spending a little time thinking about how you mark time, and what would be useful in a clock of your own design.

**Please indicate anyone you collaborated with on this Lab here.**
Be generous in acknowledging their contributions! And also recognizing any other influences (e.g. from YouTube, Github, Twitter) that informed your design. 

Hong and Yun-Chung both worked on setting up the Pi, along with brainstorming the storyboards for the clocks.

## Prep

1. ### Set up your Lab 2 Github

At the start of lab Wednesday, ensure you have the latest lab content by updating your forked repository. 

**📖 [Follow the step-by-step guide for safely updating your fork](pull_updates/README.md)**

This guide covers how to pull updates without overwriting your completed work, handle merge conflicts, and recover if something goes wrong.


2. ### Get Kit and Inventory Parts
Take inventory of the kit parts that you have, and note anything that is missing:

***Update your [parts list inventory](partslist.md)***

3. ### Prepare your Pi for lab this week
[Follow these instructions](prep.md) to download and burn the image for your Raspberry Pi before lab Wednesday.




## Overview
For this assignment, you are going to 

A) [Connect to your Pi](#part-a)  

B) [Try out cli_clock.py](#part-b) 

C) [Set up your RGB display](#part-c)

D) [Try out clock_display_demo](#part-d) 

E) [Modify the code to make the display your own](#part-e)

F) [Make a short video of your modified barebones PiClock](#part-f)

G) [Sketch and brainstorm further interactions and features you would like for your clock for Part 2.](#part-g)

## The Report
This readme.md page in your own repository should be edited to include the work you have done. You can delete everything but the headers and the sections between the \*\*\***stars**\*\*\*. Write the answers to the questions under the starred sentences. Include any material that explains what you did in this lab hub folder, and link it in the readme.

Labs are due on Sunday midnight. Make sure this page is linked to on your main class hub page.

## Part A. 
### Connect to your Pi
Just like you did in the lab prep, ssh on to your pi. Once you get there, create a Python environment (named venv) by typing the following commands.

```
ssh pi@<your Pi's IP address>
...
pi@raspberrypi:~ $ python -m venv venv
pi@raspberrypi:~ $ source venv/bin/activate
(venv) pi@raspberrypi:~ $ 

```
### Setup Personal Access Tokens on GitHub
Set your git name and email so that commits appear under your name.
```
git config --global user.name "Your Name"
git config --global user.email "yourNetID@cornell.edu"
```

The support for password authentication of GitHub was removed on August 13, 2021. That is, in order to link and sync your own lab-hub repo with your Pi, you will have to set up a "Personal Access Tokens" to act as the password for your GitHub account on your Pi when using git command, such as `git clone` and `git push`.

Following the steps listed [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) from GitHub to set up a token. Depends on your preference, you can set up and select the scopes, or permissions, you would like to grant the token. This token will act as your GitHub password later when you use the terminal on your Pi to sync files with your lab-hub repo.


## Part B. 
### Try out the Command Line Clock
Clone your own lab-hub repo for this assignment to your Pi and change the directory to Lab 2 folder (remember to replace the following command line with your own GitHub ID):

```
(venv) pi@raspberrypi:~$ git clone https://github.com/<YOURGITID>/Interactive-Lab-Hub.git
(venv) pi@raspberrypi:~$ cd Interactive-Lab-Hub/Lab\ 2/
```
Depends on the setting, you might be asked to provide your GitHub user name and password. Remember to use the "Personal Access Tokens" you just set up as the password instead of your account one!

Check if the directory has clone sucessfully, you should see the Interactive-Lab-Hub under the home directory listed:
```
(venv) pi@raspberrypi:~ $ ls
Bookshelf      Documents            Music     Public                 venv
create_img.sh  Downloads            pi-apps   screen_boot_script.py  Videos
Desktop        Interactive-Lab-Hub  Pictures  Templates
(venv) pi@raspberrypi:~ $
```


Install the packages from the requirements.txt and run the example script `cli_clock.py`:

```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ pip install -r requirements.txt
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ python cli_clock.py 
02/24/2021 11:20:49
```

The terminal should show the time, you can press `ctrl-c` to exit the script.
If you are unfamiliar with the Python code in `cli_clock.py`, have a look at [this Python refresher](https://hackernoon.com/intermediate-python-refresher-tutorial-project-ideas-and-tips-i28s320p). If you are still concerned, please reach out to the teaching staff!


## Part C. 
### Set up your RGB Display
We have asked you to equip the [Adafruit MiniPiTFT](https://www.adafruit.com/product/4393) on your Pi in the Lab 2 prep already. Here, we will introduce you to the MiniPiTFT and Python scripts on the Pi with more details.

<img src="https://cdn-learn.adafruit.com/assets/assets/000/082/842/large1024/adafruit_products_4393_iso_ORIG_2019_10.jpg" height="200" />

The Raspberry Pi 5 has a variety of interfacing options. When you plug the pi in the red power LED turns on. Any time the SD card is accessed the green LED flashes. It has standard USB ports and HDMI ports. Less familiar it has a set of 20x2 pin headers that allow you to connect a various peripherals.

<img src="https://maker.pro/storage/g9KLAxU/g9KLAxUiJb9e4Zp1xcxrMhbCDyc3QWPdSunYAoew.png" height="400" />

To learn more about any individual pin and what it is for go to [pinout.xyz](https://pinout.xyz/pinout/3v3_power) and click on the pin. Some terms may be unfamiliar but we will go over the relevant ones as they come up.

### Hardware (you have already done this in the prep)

From your kit take out the display and the [Raspberry Pi 5](https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.raspberrypi.com%2Fproducts%2Fraspberry-pi-5%2F&psig=AOvVaw330s4wIQWfHou2Vk3-0jUN&ust=1757611779758000&source=images&cd=vfe&opi=89978449&ved=0CBMQjRxqFwoTCPi1-5_czo8DFQAAAAAdAAAAABAE)

Line up the screen and press it on the headers. The hole in the screen should match up with the hole on the raspberry pi.

<p float="left">
<img src="https://cdn-learn.adafruit.com/assets/assets/000/087/539/medium640/adafruit_products_4393_quarter_ORIG_2019_10.jpg?1579991932" height="200" />
<img src="https://cdn-learn.adafruit.com/assets/assets/000/082/861/original/adafruit_products_image.png" height="200">
</p>

### Testing your Screen

The display uses a communication protocol called [SPI](https://www.circuitbasics.com/basics-of-the-spi-communication-protocol/) to speak with the raspberry pi. We won't go in depth in this course over how SPI works. The port on the bottom of the display connects to the SDA and SCL pins used for the I2C communication protocol which we will cover later. GPIO (General Purpose Input/Output) pins 23 and 24 are connected to the two buttons on the left. GPIO 22 controls the display backlight.

To show you the IP and Mac address of the Pi to allow connecting remotely we created a service that launches a python script that runs on boot. For the following steps stop the service by typing ``` sudo systemctl stop piscreen.service --now```. Othwerise two scripts will try to use the screen at once. You may start it again by typing ``` sudo systemctl start piscreen.service --now```

We can test it by typing 
```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ python screen_test.py
```

You can type the name of a color then press either of the buttons on the MiniPiTFT to see what happens on the display! You can press `ctrl-c` to exit the script. Take a look at the code with
```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ cat screen_test.py
```

#### Displaying Info with Texts
You can look in `screen_boot_script.py` for how to display text on the screen!

#### Displaying an image

You can look in `image.py` for an example of how to display an image on the screen. Can you make it switch to another image when you push one of the buttons?

\*\*\***Include a picture of your own Raspberry Pi displaying the piscreen.service with your unique MAC address. Additionally, please provide another picture showing the successful completion of the screen test.**\*\*\*

### Screen test photos

The startup screen shows the Pi's network information and unique MAC address.

<img src="assets/pi-network-mac.jpg" alt="Raspberry Pi displaying its IP address, Hong network, and unique MAC address" width="720">

The MiniPiTFT displays green during the screen test.

<img src="assets/pi-screen-test-green.jpg" alt="Raspberry Pi MiniPiTFT displaying green during the screen test" width="720">

## Part D. 
### Set up the Display Clock Demo
Work on `screen_clock.py`, try to show the time by filling in the while loop (at the bottom of the script where we noted "TODO" for you). You can use the code in `cli_clock.py` and `stats.py` to figure this out.

### Working clock

The completed [screen_clock.py](screen_clock.py) displays the date and time on the MiniPiTFT.

<img src="assets/pi-clock-demo.jpg" alt="Raspberry Pi displaying the date and time on a red background" width="720">

### How to Edit Scripts on Pi
Option 1. One of the ways for you to edit scripts on Pi through terminal is using [`nano`](https://linuxize.com/post/how-to-use-nano-text-editor/) command. You can go into the `screen_clock.py` by typing the follow command line:
```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ nano screen_clock.py
```
You can make changes to the script this way, remember to save the changes by pressing `ctrl-o` and press enter again. You can press `ctrl-x` to exit the nano mode. There are more options listed down in the terminal you can use in nano.

Option 2. Another way for you to edit scripts is to use VNC on your laptop to remotely connect your Pi. Try to open the files directly like what you will do with your laptop and edit them. Since the default OS we have for you does not come up a python programmer, you will have to install one yourself otherwise you will have to edit the codes with text editor. [Thonny IDE](https://thonny.org/) is a good option for you to install, try run the following command lines in your Pi's ternimal:

  ```
  pi@raspberrypi:~ $ sudo apt install thonny
  pi@raspberrypi:~ $ sudo apt update && sudo apt upgrade -y
  ```

Now you should be able to edit python scripts with Thonny on your Pi.

Option 3. A nowadays often preferred method is to use Microsoft [VS code to remote connect to the Pi](https://www.raspberrypi.com/news/coding-on-raspberry-pi-remotely-with-visual-studio-code/). This gives you access to a fullly equipped and responsive code editor with terminal and file browser.  

Pro Tip: Using tools like [code-server](https://coder.com/docs/code-server/latest) you can even setup a VS Code coding environment hosted on your raspberry pi and code through a web browser on your tablet or smartphone! 

## Part E. Read Part 2. Sketch and brainstorm further interactions and features you would like for your clock.

One potential source of ideas might be thinking about other clocks and timekeeping devices for inspiration.

Another might be novel units of time. How do you measure a year? [In daylights? In midnights? In cups of coffee?](https://www.youtube.com/watch?v=wsj15wPpjLY)

We strongly discourage literal digital or analog clock display: Be creative.


### Idea 1: Sun and moon clock

The sun and moon move across the display to represent early morning, noon, evening, and midnight.

<img src="assets/storyboard-sun-moon.jpg" alt="Four-panel storyboard showing the sun and moon moving across the sky throughout the day" width="960">

### Idea 2: Daily routine clock

An animated character represents the time of day through activities: sleeping early in the morning, running in the afternoon, reading in the evening, and returning to bed at night. The background changes with the time of day.

<img src="assets/storyboard-daily-routine.jpg" alt="Four-panel storyboard of a character sleeping, running, reading, and returning to bed" width="960">

### Idea 3: Coffee clock

Coffee becomes colder as the day goes on, changing from a steaming cup to an iced drink as a visual representation of passing time.

<img src="assets/storyboard-coffee.jpg" alt="Two-panel storyboard showing hot coffee transitioning to an iced drink as the day progresses" width="960">


**Put the names of the people you gave feedback to here. (Even better, add links to their repos here!)**

### Feedback on classmates’ designs

**[Jiesen Huang — Orange laundry timer](https://github.com/certaindragon3/Interactive-Lab-Hub/tree/Fall2026/Lab%202)**

I like how the ripening oranges connect time to a daily routine. Using two oranges for washing and three for drying also makes the modes visually distinct. One thing to clarify is how much time each fruit represents: A button-triggered view of the remaining minutes could help someone decide whether they have time to leave the room. I would also test whether the completion signal is noticeable from where the device normally sits.

**[Jovian — Plant clock](https://github.com/jovianw/Interactive-Lab-Hub/tree/Fall2026/Lab%202)**

I like the progression from a small plant to a flowering plant throughout the day. The moving sun helps explain the connection between growth and time. However, the nighttime panel could be clearer: an empty pot might look like the clock reset. Also, keeping the plant visible with a closed flower and darker background could communicate that it is resting. It would also help to clarify whether leaves appear at specific hours or the plant grows continuously.

**[Alexander Yen and David Zhang — NYC Sun and Moon Clock](https://github.com/Alexyen04/Alex-Yen-Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md)**

I like how the NYC skyline gives the clock a personal connection to the city. The button for checking the exact time makes the visual concept practical. I would include that interaction in the storyboard, showing what appears after pressing the button and how the display returns to the skyline. I would also check whether the skyline leaves enough space for the sun and moon to remain visible near the horizon.

### Feedback received on our design

**Jiesen Huang**

The sun and moon make the general time of day easy to understand. I would clarify how their positions correspond to specific times. For example, when does the sun rise, when does it reach the top, and when does the moon appear? It would also help to distinguish a repeating demonstration animation from a clock that follows the actual time.

**Jovian**

I like the changes between morning, afternoon, and night. One thing to consider is whether someone can distinguish early evening from late night just by looking at the moon. Combining its position with changes in the background color could make those stages clearer.

**Alexander Yen and David Zhang**

The sun and moon give a clear general sense of the time of day. Since the original storyboards only show the animation, adding a button to briefly reveal the exact time could make the clock more practical. A follow-up diagram could show how the user activates this feature and returns to the sky view.


# Lab 2 Part 2

## Prep 

1. Pick up remaining parts for kit on Wednesday lab class. Check the updated [parts list inventory](partslist.md) and let the TA know if there is any part missing.

2. Look at and give feedback on the Part E. for at least 3 other people in the class and get 3 people to comment on your Part E!)
**Put the feedback for your ideas here.**

## Update your Lab Hub

[Update your Lab Hub](pull_updates/README.md) to get the latest content and requirements for Part 2.

## Modify the barebones clock to make it your own

Start small, pick just one element of your overall idea, just to show you have a handle on the code and components.

\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

My code (version 1): [sun_moon_clock_barebones.py](sun_moon_clock_barebones.py)

For the first pass I took the single simplest piece of the storyboard: one circle in the middle of the screen that turns from the sun into the moon and back again. It starts as a full yellow sun, the yellow fades to white, and then a bite is taken out of it until all that is left is a crescent moon, before the whole thing runs in reverse. Nothing moves and nothing else is drawn — no sky, no horizon, no stars — and there is nothing to press. It just runs on its own.

> **AI Disclaimer:** The code for this clock (`sun_moon_clock_barebones.py`) was partially written with help from AI (Claude Code). The sun-and-moon idea and the overall design are mine. The AI helped with:
> - **Colors:** choosing the sun's yellow and the moon's white, and fading one into the other.
> - **The crescent:** the math that slides a background colored circle across the sun to bite a crescent moon out of it.
> - **Checking the code:** making sure the script runs without errors.

## Make a short video of your modified barebones PiClock

\*\*\***Take a video of your barely modified PiClock.**\*\*\*

https://drive.google.com/file/d/1wfe_Dz2i2TEp0cg_r9VugkZTJMRL6giC/view?usp=sharing

After you edit and work on the scripts for Lab 2, the files should be upload back to your own GitHub repo! You can push to your personal github repo by adding the files here, commiting and pushing.

```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ git add .
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ git commit -m 'your commit message here'
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ git push
```

After that, Git will ask you to login to your GitHub account to push the updates online, you will be asked to provide your GitHub user name and password. Remember to use the "Personal Access Tokens" you set up in Part A as the password instead of your account one! Go on your GitHub repo with your laptop, you should be able to see the updated files from your Pi!

## Now, make your own PiClock

Do take advantage of having done the previous iteration to refine and simplify your design.

** Insert any updates ideas, sketches, [Verplank diagrams](https://ccrma.stanford.edu/courses/250a-fall-2004/IDSketchbok.pdf))!, storyboards for your ideas **

### Verplank diagram

<img src="assets/verplank-sun-moon.svg" alt="Verplank interaction diagram for the sun and moon clock: holding the top button freezes the sky and shows the exact time" width="960">

**How do you do?** Hold down the top button. That is the only control — a discrete handle worth one bit, held or not held. The rest of the time the clock runs untouched.

**How do you feel?** The sky answers on the screen. Normally the sun and moon drift along the arc and the colors shift from morning blue to sunset orange to a starry night. While the button is held, the motion freezes and the exact time appears at the top of the screen. Let go and it picks up from where it stopped, so nothing is lost by checking.

**How do you know?** The sky is the dial, and everyone already knows how to read one: the sun comes up on the left, stands overhead at noon, goes down on the right, and the moon carries the night back around to dawn. That gets you the rough time at a glance. The button is the escape hatch for when a glance is not enough and you want the number.


\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

My code (version 2): [sun_moon_clock.py](sun_moon_clock.py)

Version 2 keeps the sky from version 1 and adds the one interaction from the Verplank diagram above. Holding the top button freezes the sun or moon wherever it is on the arc and prints the exact time at the top of the screen; letting go picks the animation back up from the same point, so checking the time never costs you your place. Sunrise is mapped to 6:00, which makes one lap of the arc a full 24 hour day.

> **AI Disclaimer:** The code for this clock (`sun_moon_clock.py`) was partially written with help from AI (Claude Code). The sun-and-moon idea, the overall design, and the hold-to-read-the-time interaction are mine. The AI helped with:
> - **Visuals:** the sky colors changing through the day, the sun's glow and rays, the stars, and the crescent shape as the sun turns into the moon.
> - **Coordinates:** the math that places the sun and moon along the half-circle path above the horizon.
> - **Smooth animation:** timing the loop so the sun and moon move and change color smoothly rather than jumping.
> - **The button:** wiring the top button to pause the animation, mapping the paused position to a time of day, and drawing the time label so it stays readable against any sky.
> - **Checking the code:** making sure the script runs without errors.

\*\*\***Take a video of your PiClock.**\*\*\*

https://drive.google.com/file/d/1DWziLtjnoy_EH5faDNd79GSs4AHTSyXU/view?usp=sharing


As always, make sure you document contributions and ideas from others (and AI) explicitly in your writeup.

You are permitted (but not required) to work in groups and share a turn in; you are expected to make equal contribution on any group work you do, and N people's group project should look like N times the work of a single person's lab.  Make sure the page for the group turn in is linked to your personal Interactive Lab Hub page. 


