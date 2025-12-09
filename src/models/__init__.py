"""
Models module for fashion compatibility learning
"""

from .train.model_training import FashionCLIPModel, TripletLoss, FashionTrainer

__all__ = ['FashionCLIPModel', 'TripletLoss', 'FashionTrainer']
