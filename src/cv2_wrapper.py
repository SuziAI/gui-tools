import cv2

WINDOW_GUI_NORMAL = cv2.WINDOW_GUI_NORMAL
EVENT_RBUTTONDOWN = cv2.EVENT_RBUTTONDOWN
EVENT_MOUSEMOVE = cv2.EVENT_MOUSEMOVE
EVENT_RBUTTONUP = cv2.EVENT_RBUTTONUP
WND_PROP_VISIBLE = cv2.WND_PROP_VISIBLE
BORDER_CONSTANT = cv2.BORDER_CONSTANT
COLOR_BGR2RGB = cv2.COLOR_BGR2RGB

def namedWindow(*args, **kwargs):
    return cv2.namedWindow(*args, **kwargs)
def setMouseCallback(*args, **kwargs):
    return cv2.setMouseCallback(*args, **kwargs)
def destroyWindow(*args, **kwargs):
    return cv2.namedWindow(*args, **kwargs)
def waitKey(*args, **kwargs):
    return cv2.waitKey(*args, **kwargs)
def getWindowProperty(*args, **kwargs):
    return cv2.getWindowProperty(*args, **kwargs)
def rectangle(*args, **kwargs):
    return cv2.rectangle(*args, **kwargs)
def imshow(*args, **kwargs):
    return cv2.imshow(*args, **kwargs)
def imread(*args, **kwargs):
    return cv2.imread(*args, **kwargs)
def cvtColor(*args, **kwargs):
    return cv2.cvtColor(*args, **kwargs)
def copyMakeBorder(*args, **kwargs):
    return cv2.copyMakeBorder(*args, **kwargs)
def hconcat(*args, **kwargs):
    return cv2.hconcat(*args, **kwargs)
def split(*args, **kwargs):
    return cv2.split(*args, **kwargs)
def merge(*args, **kwargs):
    return cv2.merge(*args, **kwargs)