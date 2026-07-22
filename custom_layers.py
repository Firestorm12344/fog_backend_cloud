import tensorflow as tf
from tensorflow.keras import layers


class TimeSeriesAugment(layers.Layer):
    def __init__(self, noise_std=0.05, jitter_amp=0.02, drop_prob=0.10, **kwargs):
        super().__init__(**kwargs)
        self.noise_std = noise_std
        self.jitter_amp = jitter_amp
        self.drop_prob = drop_prob

    def call(self, x, training=None):
        if training:
            x = x + tf.random.normal(tf.shape(x), stddev=self.noise_std)
            x = x + tf.random.uniform(tf.shape(x), -self.jitter_amp, self.jitter_amp)
            mask = tf.cast(tf.random.uniform(tf.shape(x)) > self.drop_prob, x.dtype)
            x = x * mask
        return x
