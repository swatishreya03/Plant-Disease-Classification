# -*- coding: utf-8 -*-
"""plant_disease_classification.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1DjM9mIvZS5u3xKoCEFxDP2DQrDIW_moQ

# Potato Disease Classification
"""

# prompt: mount drive

from google.colab import drive
drive.mount('/content/drive')

"""### Import all the Dependencies"""

import tensorflow as tf
from tensorflow.keras import models, layers
import matplotlib.pyplot as plt
from IPython.display import HTML

"""### Set all the Constants"""

BATCH_SIZE = 32
IMAGE_SIZE = 256
CHANNELS=3
EPOCHS=50

"""### Import data into tensorflow dataset object"""

dataset = tf.keras.preprocessing.image_dataset_from_directory(
    "/content/drive/MyDrive/PlantVillage",  # Directory path where the dataset is located
    seed=123,  # Seed for random shuffling of the dataset
    shuffle=True,  # Whether to shuffle the data or not
    image_size=(IMAGE_SIZE,IMAGE_SIZE),  # Desired image size for resizing
    batch_size=BATCH_SIZE  # Number of images in each batch
)

class_names = dataset.class_names
class_names

for image_batch, labels_batch in dataset.take(1):
    print(image_batch.shape)  # Prints the shape of the image batch
    print(labels_batch.numpy())  # Prints the labels batch as a NumPy array

"""### Visualize some of the images from our dataset"""

plt.figure(figsize=(12, 12))  # Sets the figure size for the plot

for image_batch, labels_batch in dataset.take(1):  # Iterates over the first batch of images and labels in the dataset
    for i in range(12):  # Iterates over the images in the batch (assumes batch size of 12)
        ax = plt.subplot(3, 4, i + 1)  # Creates a subplot with 3 rows and 4 columns, and selects the i+1th subplot
        plt.imshow(image_batch[i].numpy().astype("uint8"))  # Displays the i-th image in the batch as a NumPy array
        plt.title(class_names[labels_batch[i]])  # Sets the title of the subplot to the corresponding label from the batch
        plt.axis("off")  # Turns off the axis labels and ticks for the subplot

len(dataset)

train_size = 0.8
len(dataset)*train_size

train_ds = dataset.take(516)
len(train_ds)

test_ds = dataset.skip(516)
len(test_ds)

val_size=0.1
len(dataset)*val_size

val_ds = test_ds.take(64)
len(val_ds)

test_ds = test_ds.skip(64)
len(test_ds)

def get_dataset_partitions_tf(ds, train_split=0.8, val_split=0.1, test_split=0.1, shuffle=True, shuffle_size=10000):
    assert (train_split + test_split + val_split) == 1  # Ensures that the split ratios add up to 1

    ds_size = len(ds)  # Gets the total size of the dataset

    if shuffle:
        ds = ds.shuffle(shuffle_size, seed=12)  # Shuffles the dataset if `shuffle` is True, using a specified `shuffle_size` and seed

    train_size = int(train_split * ds_size)  # Calculates the size of the training set based on the split ratio
    val_size = int(val_split * ds_size)  # Calculates the size of the validation set based on the split ratio

    train_ds = ds.take(train_size)  # Takes the first `train_size` elements from the shuffled dataset as the training set
    val_ds = ds.skip(train_size).take(val_size)  # Skips the training set elements and takes the next `val_size` elements as the validation set
    test_ds = ds.skip(train_size).skip(val_size)  # Skips the training and validation set elements and takes the rest as the test set

    return train_ds, val_ds, test_ds  # Returns the training, validation, and test sets

train_ds, val_ds, test_ds = get_dataset_partitions_tf(dataset)

len(train_ds)

len(val_ds)

len(test_ds)

"""### Cache, Shuffle, and Prefetch the Dataset"""

train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=tf.data.AUTOTUNE)
val_ds = val_ds.cache().shuffle(1000).prefetch(buffer_size=tf.data.AUTOTUNE)
test_ds = test_ds.cache().shuffle(1000).prefetch(buffer_size=tf.data.AUTOTUNE)

"""## Building the Model

### Creating a Layer for Resizing and Normalization
Before we feed our images to network, we should be resizing it to the desired size.
Normalizing the image pixel value (keeping them in range 0 and 1 by dividing by 256) to omprove model performance.
"""

from tensorflow.keras import layers
import tensorflow as tf

resize_and_rescale = tf.keras.Sequential([
  layers.Resizing(IMAGE_SIZE, IMAGE_SIZE),
  layers.Rescaling(1./255),
])

"""### Data Augmentation
Data Augmentation is needed when we have less data, this boosts the accuracy of our model by augmenting the data.
"""

import tensorflow as tf
from tensorflow.keras import layers

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),  # Randomly flips the input images horizontally and vertically
    layers.RandomRotation(0.2),  # Randomly applies rotations to the input images within a range of 0.2 radians
])

"""#### Applying Data Augmentation to Train Dataset"""

train_ds = train_ds.map(
    lambda x, y: (data_augmentation(x, training=True), y)
).prefetch(buffer_size=tf.data.AUTOTUNE)

"""### Model Architecture
We use a CNN coupled with a Softmax activation in the output layer. We also add the initial layers for resizing, normalization and Data Augmentation.
"""

n_classes = 10

model = tf.keras.Sequential([
    layers.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, CHANNELS)),  # Input layer with specified input shape
    resize_and_rescale,  # Preprocessing layer for resizing and rescaling the input images
    layers.Conv2D(32, kernel_size=(3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, kernel_size=(3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, kernel_size=(3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(n_classes, activation='softmax'),
])

model.summary()

"""### Compiling the Model
We use `adam` Optimizer, `SparseCategoricalCrossentropy` for losses, `accuracy` as a metric
"""

model.compile(
    optimizer='adam',
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False),
    metrics=['accuracy']
)

history = model.fit(
    train_ds,
    batch_size=BATCH_SIZE,
    validation_data=val_ds,
    verbose=1,
    epochs=10,
)

scores = model.evaluate(test_ds)

scores

"""Scores is just a list containing loss and accuracy value

### Plotting the Accuracy and Loss Curves
"""

history

history.params

history.history.keys()

type(history.history['loss'])

len(history.history['loss'])

history.history['loss'][:10] # show loss for first 5 epochs

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

loss = history.history['loss']
val_loss = history.history['val_loss']

plt.figure(figsize=(8, 8))
plt.subplot(1, 2, 1)
plt.plot(range(len(acc)), acc, label='Training Accuracy')
plt.plot(range(len(val_acc)), val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.title('Training and Validation Accuracy')

plt.subplot(1, 2, 2)
plt.plot(range(len(loss)), loss, label='Training Loss')
plt.plot(range(len(val_loss)), val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.title('Training and Validation Loss')
plt.show()

"""### Run prediction on a sample image"""

import numpy as np
for images_batch, labels_batch in test_ds.take(1):

    first_image = images_batch[0].numpy().astype('uint8')
    first_label = labels_batch[0].numpy()

    print("first image to predict")
    plt.imshow(first_image)
    print("actual label:",class_names[first_label])

    batch_prediction = model.predict(images_batch)
    print("predicted label:",class_names[np.argmax(batch_prediction[0])])

"""### Write a function for inference"""

def predict(model, img):
    img_array = tf.keras.preprocessing.image.img_to_array(images[i].numpy())
    img_array = tf.expand_dims(img_array, 0)

    predictions = model.predict(img_array)

    predicted_class = class_names[np.argmax(predictions[0])]
    confidence = round(100 * (np.max(predictions[0])), 2)
    return predicted_class, confidence

"""**Now run inference on few sample images**"""

plt.figure(figsize=(15, 15))
for images, labels in test_ds.take(1):
    for i in range(9):
        ax = plt.subplot(3, 3, i + 1)
        plt.imshow(images[i].numpy().astype("uint8"))

        predicted_class, confidence = predict(model, images[i].numpy())
        actual_class = class_names[labels[i]]

        plt.title(f"Actual: {actual_class},\n Predicted: {predicted_class}.\n Confidence: {confidence}%")

        plt.axis("off")