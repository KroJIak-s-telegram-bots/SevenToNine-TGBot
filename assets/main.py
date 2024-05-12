import cv2
import os

assetFileName = 'kartochki-7x9-04-ico.jpg'
folder = 'cards'

img = cv2.imread(assetFileName)
img = img[16:-16, 19:-19]
stepH, stepW = 224, 150
spaceH, spaceW = 2, 5

for i in range(3):
    for j in range(3):
        simg = img.copy()
        simg = simg[i*(stepH+spaceH):i*(stepH+spaceH)+stepH, j*(stepW+spaceW):j*(stepW+spaceW)+stepW]
        simg = cv2.resize(simg, (stepW, stepH))
        countImages = len(os.listdir(folder))
        cv2.imwrite(f'{folder}/{countImages+1}.png', simg)