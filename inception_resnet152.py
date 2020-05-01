import math
import keras
import pickle
import numpy as np
import tensorflow as tf
import keras.backend as K
from keras.models import Model
from keras.utils import np_utils
from keras.optimizers import SGD
from keras.layers.core import Layer
from keras.callbacks import LearningRateScheduler
from sklearn.model_selection import train_test_split
from keras.layers import Conv2D, MaxPool2D, Dropout,\
Dense, Input, concatenate,GlobalAveragePooling2D, AveragePooling2D, Flatten


def inception_module(x, filters_1x1, filters_3x3_reduce, filters_3x3, filters_5x5_reduce, filters_5x5, filters_pool_proj, name=None):
	kernel_init = keras.initializers.glorot_uniform()
	bias_init = keras.initializers.Constant(value=0.2)
	conv_1x1 = Conv2D(filters_1x1, (1, 1), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(x)
	conv_3x3 = Conv2D(filters_3x3_reduce, (1, 1), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(x)
	conv_3x3 = Conv2D(filters_3x3, (3, 3), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(conv_3x3)
	conv_5x5 = Conv2D(filters_5x5_reduce, (1, 1), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(x)
	conv_5x5 = Conv2D(filters_5x5, (5, 5), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(conv_5x5)
	pool_proj = MaxPool2D((3, 3), strides=(1, 1), padding='same')(x)
	pool_proj = Conv2D(filters_pool_proj, (1, 1), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(pool_proj)
	output = concatenate([conv_1x1, conv_3x3, conv_5x5, pool_proj], axis=3, name=name)	
	return output


def resnet152_model(img_rows, img_cols, color_type=1, num_classes=None):
	kernel_init = keras.initializers.glorot_uniform()
	bias_init = keras.initializers.Constant(value=0.2)
	input_layer = Input(shape=(img_rows, img_cols, color_type), name='data')
	x = Conv2D(64, (7, 7), padding='same', strides=(2, 2), activation='relu', name='conv_1_7x7/2', kernel_initializer=kernel_init, bias_initializer=bias_init)(input_layer)
	x = MaxPool2D((3, 3), padding='same', strides=(2, 2), name='max_pool_1_3x3/2')(x)
	x = Conv2D(64, (1, 1), padding='same', strides=(1, 1), activation='relu', name='conv_2a_3x3/1')(x)
	x = Conv2D(192, (3, 3), padding='same', strides=(1, 1), activation='relu', name='conv_2b_3x3/1')(x)
	x = MaxPool2D((3, 3), padding='same', strides=(2, 2), name='max_pool_2_3x3/2')(x)

	x = inception_module(x,
		filters_1x1=64,
		filters_3x3_reduce=96,
		filters_3x3=128,
		filters_5x5_reduce=16,
		filters_5x5=32,
		filters_pool_proj=32,
		name='inception_3a')

	x = inception_module(x,
		filters_1x1=128,
		filters_3x3_reduce=128,
		filters_3x3=192,
		filters_5x5_reduce=32,
		filters_5x5=96,
		filters_pool_proj=64,
		name='inception_3b')

	x = MaxPool2D((3, 3), padding='same', strides=(2, 2), name='max_pool_3_3x3/2')(x)

	x = inception_module(x,
		filters_1x1=192,
		filters_3x3_reduce=96,
		filters_3x3=208,
		filters_5x5_reduce=16,
		filters_5x5=48,
		filters_pool_proj=64,
		name='inception_4a')

	x1 = AveragePooling2D((5, 5), strides=3)(x)
	x1 = Conv2D(128, (1, 1), padding='same', activation='relu')(x1)
	x1 = Flatten()(x1)
	x1 = Dense(1024, activation='relu')(x1)
	x1 = Dropout(0.7)(x1)
	x1 = Dense(3, activation='softmax', name='auxilliary_output_1')(x1)

	x = inception_module(x,
		filters_1x1=160,
		filters_3x3_reduce=112,
		filters_3x3=224,
		filters_5x5_reduce=24,
		filters_5x5=64,
		filters_pool_proj=64,
		name='inception_4b')

	x = inception_module(x,
		filters_1x1=128,
		filters_3x3_reduce=128,
		filters_3x3=256,
		filters_5x5_reduce=24,
		filters_5x5=64,
		filters_pool_proj=64,
		name='inception_4c')

	x = inception_module(x,
		filters_1x1=112,
		filters_3x3_reduce=144,
		filters_3x3=288,
		filters_5x5_reduce=32,
		filters_5x5=64,
		filters_pool_proj=64,
		name='inception_4d')

	x2 = AveragePooling2D((5, 5), strides=3)(x)
	x2 = Conv2D(128, (1, 1), padding='same', activation='relu')(x2)
	x2 = Flatten()(x2)
	x2 = Dense(1024, activation='relu')(x2)
	x2 = Dropout(0.7)(x2)
	x2 = Dense(3, activation='softmax', name='auxilliary_output_2')(x2)

	x = inception_module(x,
		filters_1x1=256,
		filters_3x3_reduce=160,
		filters_3x3=320,
		filters_5x5_reduce=32,
		filters_5x5=128,
		filters_pool_proj=128,
		name='inception_4e')

	x = MaxPool2D((3, 3), padding='same', strides=(2, 2), name='max_pool_4_3x3/2')(x)

	x = inception_module(x,
		filters_1x1=256,
		filters_3x3_reduce=160,
		filters_3x3=320,
		filters_5x5_reduce=32,
		filters_5x5=128,
		filters_pool_proj=128,
		name='inception_5a')

	x = inception_module(x,
		filters_1x1=384,
		filters_3x3_reduce=192,
		filters_3x3=384,
		filters_5x5_reduce=48,
		filters_5x5=128,
		filters_pool_proj=128,
		name='inception_5b')

	x = GlobalAveragePooling2D(name='avg_pool_5_3x3/1')(x)
	x = Dropout(0.4)(x)
	x = Dense(num_classes, activation='softmax', name='fc')(x)	

	weights_path = 'models/resnet152_weights_tf.h5'
	model = Model(input_layer, x)
	model.load_weights(weights_path, by_name=True)
	sgd = SGD(lr=1e-3, decay=1e-6, momentum=0.9, nesterov=True)
	model.compile(optimizer=sgd, loss='categorical_crossentropy', metrics=['accuracy'])
	return model


if __name__ == '__main__':
	num_classes = 3
	X = pickle.load(open("X_rgb.pickle", "rb"))
	y = pickle.load(open("y_rgb.pickle", "rb"))
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=2)
	img_rows, img_cols, channels = X_train[0].shape[0], X_train[0].shape[1], X_train[0].shape[2]
	epochs = int(input('Epochs: '))
	batch_size = int(input('Batch Size: '))
	model = resnet152_model(img_rows, img_cols, channels, num_classes)
	model.fit(X_train, y_train,
		batch_size=batch_size,
		nb_epoch=epochs,
		shuffle=True,
		verbose=1,
		validation_data=(X_test, y_test),)