import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import LabelBinarizer, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam,SGD,Adagrad,Adadelta,RMSprop
from keras.utils import to_categorical
from keras.layers import Dropout, Flatten,Activation
from keras.layers import Conv2D, MaxPooling2D, BatchNormalization
from keras.metrics import Precision

import tensorflow as tf  # supports till python version 3.11.x, does not work on python 3.12 (10th January,2024) 
import random as rn 

# specifically for manipulating zipped images and getting numpy arrays of pixel values of images.
import cv2
from tqdm import tqdm
import os
from random import shuffle
from zipfile import ZipFile
from PIL import Image


DIR = rf"{os.path.dirname(__file__)}"
X=[]
Z=[]
IMG_SIZE=150

#assuming dataset folder is in the same folder as this file
noFire_DIR= rf"{DIR}\wildfire_detection_dataset\noFire" 
Fire_DIR= rf"{DIR}\wildfire_detection_dataset\Fire"

def assign_label(img, imgCls):
	return imgCls

def make_train_data(imgCls, DIR):
    for img in tqdm(os.listdir(DIR)):
        label= assign_label(img, imgCls)
        path = os.path.join(DIR, img)
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

        X.append(np.array(img))
        Z.append(str(label))

make_train_data('Fire', Fire_DIR)
print(len(X))

make_train_data('noFire',noFire_DIR)
print(len(X))
''' 
fig, ax = plt.subplots(2,2)

fig.set_size_inches(15,15)

for i in range(2):
    for j in range (2):
        l=rn.randint(0,len(Z))
        ax[i,j].imshow(X[l])
        ax[i,j].set_title('Forest: '+Z[l])

plt.tight_layout ()
'''
'''lb = LabelBinarizer()
labels = lb.fit_transform(labels)
labels = to_categorical(labels)
'''

'''
le=LabelEncoder()
Y=le.fit_transform(Z)
Y=to_categorical(Y,2)
'''

lb=LabelBinarizer()
Y=lb.fit_transform(Z)
Y=to_categorical(Y,2)
X=np.array(X)
X=X/255

x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.25, random_state=42)
print(len(x_train), len(x_test))

np.random.seed(42)
rn.seed(42) #usage?
tf.random.set_seed(42)

model = Sequential()
model.add(Conv2D(filters = 32, kernel_size = (5,5),padding = 'Same',activation ='relu', input_shape = (150, 150, 3)))
model.add(MaxPooling2D(pool_size=(2,2)))
# conv2D is 2D i.e. Good for Images -;\bo Elteef
model.add(Conv2D(filters = 64, kernel_size = (3,3),padding = 'Same',activation ='relu'))
model.add(MaxPooling2D(pool_size=(2,2), strides=(2,2)))
model.add(Conv2D(filters =96, kernel_size = (3,3),padding = 'Same',activation ='relu'))
model.add(MaxPooling2D(pool_size=(2,2), strides=(2,2)))
model.add(Conv2D(filters = 96, kernel_size = (3,3),padding = 'Same',activation ='relu'))
model.add(MaxPooling2D(pool_size=(2,2), strides=(2,2)))
model.add(Flatten())
model.add(Dense(512))
model.add(Activation('relu'))
model.add(Dense(2, activation = "softmax"))

#from keras.utils.vis_utils import plot_model
#plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)

batch_size = 16  # 32 #64 #128
epochs=10

from keras.callbacks import ReduceLROnPlateau
red_lr= ReduceLROnPlateau(monitor='val_acc' ,patience=3,verbose=1,factor=0.1) #usage?

datagen = ImageDataGenerator(
    featurewise_center=False, # set input mean toe over the dataset
    samplewise_center=False, # set each sample mean toe
    featurewise_std_normalization = False, # divide inputs by std of the dataset
    samplewise_std_normalization=False, # divide each input by its std
    zca_whitening=False, # apply ZCA whitening
    rotation_range = 0.2, # randomly rotate images in the range (degrees, e to 180)
    zoom_range = 0.1, # Randomly zoom image
    width_shift_range=0.2, # randomly shift images horizontally (fraction of total width)
    height_shift_range=0.2, # randomly shift images vertically (fraction of total height)
    horizontal_flip=False, # randomly flip images
    vertical_flip=True) # randomly flip images

model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['AUC', 'accuracy'])  #Precision(thresholds=0), 

model.summary()
print(model.summary())

History = model.fit(datagen.flow(x_train, y_train, batch_size = batch_size),
    epochs = epochs, validation_data = (x_test,y_test),
    verbose = 1, steps_per_epoch = x_train.shape[0] // batch_size)

plt.plot(History.history['loss'])
plt.plot(History.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epochs')
plt.legend([ 'train', 'test'])
plt.show()

plt.plot(History.history['accuracy'])
plt.plot(History.history['val_accuracy'])
plt.title('Model accuracy')
plt.ylabel('accuracy')
plt.xlabel('Epochs')
plt.legend([ 'train', 'test'])
plt.show()

plt.plot(History.history['auc'])
plt.plot(History.history['val_auc'])
plt.title('Model AUC')
plt.ylabel('AUC')
plt.xlabel('Epochs')
plt.legend([ 'train', 'test'])
plt.show()

# make predictions on the testing set
print("[INFO] evaluating network ... ")
predidxs = model.predict(x_test, batch_size=batch_size)
predidxs = np.argmax(predidxs, axis = 1)

print(classification_report(y_test.argmax(axis = 1), predidxs, target_names = lb.classes_))

y_test=np.argmax(y_test, axis=1)
#Create confusion matrix and normalizes it over predicted (columns)
cm = confusion_matrix(y_test, predidxs , normalize='pred')
print(cm)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels = lb.classes_)
disp.plot()
plt.show()



N = epochs
plt.style.use("ggplot")
plt.figure()
plt.plot(np.arange(0, N), History.history["loss"], label="train_loss")
plt.plot(np.arange(0, N), History.history["val_loss"], label="val_loss")
plt.plot(np.arange(0, N), History.history["accuracy"], label="train_acc")
plt.plot(np.arange(0, N), History.history["val_accuracy"], label="val_acc")
plt.title("Training Loss and Accuracy")
plt.xlabel("Epoch #")
plt.ylabel("Loss/Accuracy")
plt.legend(loc="lower left")
plt.savefig("plot5.png")
plt.show()

a=1