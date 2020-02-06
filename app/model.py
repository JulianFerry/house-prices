import pandas as pd
import numpy as np

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor

import joblib


class HousePrices:

    def __init__(self):
        """ Defines features to use and creates modelling pipeline """

        # Numeric data
        num_features = ['TotalBsmtSF', '1stFlrSF', '2ndFlrSF', 'OverallQual', 'YearBuilt',
                        'FullBath', 'Fireplaces', 'GarageCars', 'KitchenQual']

        # Categorical data
        cat_features = ['Foundation', 'Neighborhood']

        # Selected feature names
        self.features = num_features + cat_features + ['MSSubClass']


        # Pipelines
        idx_Fireplaces = num_features.index('Fireplaces')
        idx_GarageCars = num_features.index('GarageCars')
        idx_KitchenQual = num_features.index('KitchenQual')

        ## Numeric pipeline
        num_pipeline = Pipeline([
            ('quality_mapper', self.QualityMapper(idx_KitchenQual)),
            ('discrete_cleaner', self.DiscreteCleaner(idx_Fireplaces, idx_GarageCars)),
            ('simple_imputer', SimpleImputer()),
            ('std_scaler', StandardScaler())
        ])

        ## Generic categorical pipeline
        cat_pipeline = Pipeline([
            ('cat_imputer', SimpleImputer(strategy="most_frequent")),
            ('one_hot_encoder', OneHotEncoder())
        ])

        ## MSSubClass specific pipeline
        mssubclass_pipeline = Pipeline([
            ('cat_imputer', SimpleImputer(strategy="most_frequent")),
            ('custom_ohe', self.MSSubClassOHE())
        ])

        ## Full preprocessing pipeline
        self.preprocess_pipeline = ColumnTransformer([
            ('num', num_pipeline, num_features),
            ('cat', cat_pipeline, cat_features),
            ('mssubclass', mssubclass_pipeline, ['MSSubClass'])
        ])

        ## Model pipeline
        rf_reg = RandomForestRegressor(bootstrap=False, max_features=6, n_estimators=60)

        self.model_pipeline = Pipeline([
            ('preprocessing', self.preprocess_pipeline),
            ('model', rf_reg)
        ])


    class DiscreteCleaner(BaseEstimator, TransformerMixin):
        """ Merges infrequent values with frequent ones for discrete numeric features """

        def __init__(self, idx_Fireplaces, idx_GarageCars):
            self.idx_Fireplaces = idx_Fireplaces
            self.idx_GarageCars = idx_GarageCars

        def fit(self, X, y=None):
            return self

        def transform(self, X, y=None):
            X = np.array(X)
            X[X[:, self.idx_Fireplaces] > 2, self.idx_Fireplaces] = 2
            X[X[:, self.idx_GarageCars] > 3, self.idx_GarageCars] = 3
            return X


    class QualityMapper(BaseEstimator, TransformerMixin):
        """ Maps quality ratings into a numeric variable """

        def __init__(self, idx_KitchenQual):
            self.idx_KitchenQual = idx_KitchenQual

        def map_quality(self, array):
            quality_map = {
                'Ex': 5,
                'Gd': 4,
                'TA': 3,
                'Fa': 2,
                'Po': 1,
            }
            array[~np.isin(array, quality_map.keys())] = np.nan
            for item in quality_map.items():
                array[array == item[0]] = item[1]

        def fit(self, X, y=None):
            return self

        def transform(self, X, y=None):
            X = np.array(X)
            X[X[:, self.idx_KitchenQual] == None] = np.nan
            X[:, self.idx_KitchenQual] = self.map_quality(X[:, self.idx_KitchenQual])

            return X


    class MSSubClassOHE(BaseEstimator, TransformerMixin):
        """ Applies custom One Hot Encoding to the MSSubClass feature """

        def __init__(self):
            pass

        def fit(self, X, y=None):
            return self

        def transform(self, X, y=None):
            X = np.array(X)
            one_story = np.isin(X, [20, 30, 40, 120])
            one_half_story = np.isin(X, [45, 50, 150])
            two_story = np.isin(X, [60, 70, 160])
            two_half_story = np.isin(X, [75])
            split = np.isin(X, [80, 85, 180])
            pud = np.isin(X, [120, 150, 160, 180])
            duplex = np.isin(X, [90])
            two_family = np.isin(X, [190])

            return np.c_[np.delete(X, 0, axis=1), one_story, one_half_story,
                        two_story, two_half_story, split, pud, duplex, two_family]



    def fit(self):
        """ Fit the modelling pipeline to all of the training data """

        # Load data
        # TODO: pass source as an argument and download data from source
        housing = pd.read_csv('train.csv')
        X = housing[self.features].copy()
        y = housing['SalePrice'].copy()

        # Train model
        self.model = self.model_pipeline.fit(X, y)

    def predict(self, X, *args, **kwargs):
        """ Return model predictions for new data """

        X = X[self.features]
        return self.model.predict(X, *args, **kwargs)

