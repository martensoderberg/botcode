
# botcode
This is an attempt at controlling an arduino-powered bot ([MiniQ](https://www.dfrobot.com/wiki/index.php/4WD_MiniQ_Complete_Kit_(SKU:ROB0050))) from a raspberry pi, over a serial link.

Furthermore, it's intended for all arduino code deployment to occur over the same serial link, using the eminent [inotool](http://inotool.org/). Deployment is simply done by cloning this repository to the raspberry pi, and then running `ino build` and `ino upload` from the ardu directory.

