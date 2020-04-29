import keras
import math
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


def inception_module(x,
					 filters_1x1,
					 filters_3x3_reduce,
					 filters_3x3,
					 filters_5x5_reduce,
					 filters_5x5,
					 filters_pool_proj,
					 name=None):
	conv_1x1 = Conv2D(filters_1x1, (1, 1), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(x)
	conv_3x3 = Conv2D(filters_3x3_reduce, (1, 1), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(x)
	conv_3x3 = Conv2D(filters_3x3, (3, 3), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(conv_3x3)
	conv_5x5 = Conv2D(filters_5x5_reduce, (1, 1), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(x)
	conv_5x5 = Conv2D(filters_5x5, (5, 5), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(conv_5x5)
	pool_proj = MaxPool2D((3, 3), strides=(1, 1), padding='same')(x)
	pool_proj = Conv2D(filters_pool_proj, (1, 1), padding='same', activation='relu', kernel_initializer=kernel_init, bias_initializer=bias_init)(pool_proj)
	output = concatenate([conv_1x1, conv_3x3, conv_5x5, pool_proj], axis=3, name=name)	
	return output


def decay(epoch, steps=100):
    initial_lrate = 0.01
    drop = 0.96
    epochs_drop = 8
    lrate = initial_lrate * math.pow(drop, math.floor((1+epoch)/epochs_drop))
    return lrate


if __name__ == '__main__':
	num_classes = 3
	X = pickle.load(open("X_inception.pickle", "rb"))
	y = pickle.load(open("y_inception.pickle", "rb"))
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=2)
	# X_train =  X_train.reshape(-1, 128, 128, 3)
	
	kernel_init = keras.initializers.glorot_uniform()
	bias_init = keras.initializers.Constant(value=0.2)
	
	input_layer = Input(shape=(128, 128, 3))
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
	x = Dense(3, activation='softmax', name='output')(x)
	model = Model(input_layer, [x, x1, x2], name='inception_v1')
	# model.summary()

	epochs = int(input('Epochs: '))
	initial_lrate = float(input('Learning Rate (init): '))
	sgd = SGD(lr=initial_lrate, momentum=0.9, nesterov=False)
	lrate_scheduler = LearningRateScheduler(decay, verbose=1)
	model.compile(loss=['categorical_crossentropy', 'categorical_crossentropy',
	 'categorical_crossentropy'], loss_weights=[1, 0.3, 0.3], optimizer=sgd, metrics=['accuracy'])
	history = model.fit(X_train, [y_train, y_train, y_train], 
		validation_data=(X_test, [y_test, y_test, y_test]), epochs=epochs, batch_size=20, callbacks=[lrate_scheduler])