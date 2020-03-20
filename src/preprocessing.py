import database as db
import os
import numpy as np
import pandas as pd
import joblib

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder

DIR = os.path.abspath(os.path.dirname(__file__))


class PreProcessor(TransformerMixin):

    def __init__(self):
        """ Defines features to use and creates modelling pipeline """

        # Define features
        self._num_features = ['TotalBsmtSF', '1stFlrSF', '2ndFlrSF', 'OverallQual', 'YearBuilt',
                              'FullBath', 'Fireplaces', 'GarageCars', 'KitchenQual']
        self._cat_features = ['Foundation', 'Neighborhood']
        self.raw_features = self._num_features + self._cat_features + ['MSSubClass']

        # Create pipelines
        self._init_pipelines()

    def _init_pipelines(self):
        """ Creates modelling pipeline """

        # Pipelines
        idx_Fireplaces = self._num_features.index('Fireplaces')
        idx_GarageCars = self._num_features.index('GarageCars')
        idx_KitchenQual = self._num_features.index('KitchenQual')

        # Numeric pipeline
        num_pipeline = Pipeline([
            ('quality_mapper', _QualityMapper(idx_KitchenQual)),
            ('discrete_cleaner', _DiscreteCleaner(idx_Fireplaces, idx_GarageCars)),
            ('simple_imputer', SimpleImputer()),
            ('std_scaler', StandardScaler())
        ])

        # Categorical pipeline
        self.cat_pipeline = Pipeline([
            ('cat_imputer', SimpleImputer(strategy="most_frequent")),
            ('one_hot_encoder', OneHotEncoder())
        ])

        # MSSubClass pipeline
        mssubclass_pipeline = Pipeline([
            ('cat_imputer', SimpleImputer(strategy="most_frequent")),
            ('custom_ohe', _MSSubClassOHE())
        ])

        # Full preprocessing pipeline
        self.preprocessing_pipeline = ColumnTransformer([
            ('num', num_pipeline, self._num_features),
            ('cat', self.cat_pipeline, self._cat_features),
            ('mssubclass', mssubclass_pipeline, ['MSSubClass'])
        ])

    def fit(self, X, y=None):
        """ Fit the preprocessing pipeline to all of the training data """

        # Select features and fit preprocessing
        X = X[self.raw_features].copy()
        self.preprocessing_pipeline.fit(X)
        return self

    def transform(self, X, y=None):
        """ Return preprocessed data """

        # Preproces data
        X = X[self.raw_features].copy()
        X_pp = self.preprocessing_pipeline.transform(X)
        X_pp = pd.DataFrame(X_pp, columns=self.get_feature_names())

        return X_pp

    def get_feature_names(self):
        """
        Feature names after preprocessing.
        Replicates the get_feature_names function in the sklearn Transformer classes.
        """
        num_features = list(
            self._num_features
        )
        cat_features = list(
            self.preprocessing_pipeline
            .named_transformers_['cat']
            .named_steps['one_hot_encoder']
            .get_feature_names(self._cat_features)
        )
        mssubclass_features = list(
            self.preprocessing_pipeline
            .named_transformers_['mssubclass']
            .named_steps['custom_ohe']
            .get_feature_names()
        )
        return num_features + cat_features + mssubclass_features


class _DiscreteCleaner(BaseEstimator, TransformerMixin):
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


class _QualityMapper(BaseEstimator, TransformerMixin):
    """ Maps quality labels into a numeric variable """

    def __init__(self, idx_KitchenQual):
        self.idx_KitchenQual = idx_KitchenQual

    def map_quality(self, quality_col):
        quality_col = np.array(quality_col)
        quality_map = {
            'Ex': 5,
            'Gd': 4,
            'TA': 3,
            'Fa': 2,
            'Po': 1,
        }

        quality_col[~np.isin(quality_col, list(quality_map.keys()))] = np.nan
        for label, score in quality_map.items():
            quality_col[quality_col == label] = score

        return quality_col

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X = np.array(X)
        X[X[:, self.idx_KitchenQual] == None] = np.nan
        X[:, self.idx_KitchenQual] = self.map_quality(X[:, self.idx_KitchenQual])
        return X


class _MSSubClassOHE(BaseEstimator, TransformerMixin):
    """ Applies custom One Hot Encoding to the MSSubClass feature """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X = np.array(X)

        # Create columns of binary values based on the value of the X column
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

    def get_feature_names(self):
        """
        Feature names after preprocessing.
        Replicates the get_feature_names function in the sklearn OneHotEncoder class.
        """

        feature_names = ['MSSubClass_' + style for style in [
            'one_story', 'one_half_story',
            'two_story', 'two_half_story',
            'split', 'pud', 'duplex', 'two_family'
        ]]

        return feature_names


if __name__ == "__main__":
    from preprocessing import PreProcessor # noqa

    # Load data
    db_config = db.get_config()
    train = db.load(*db_config, 'raw_train')
    X_train = train.drop('SalePrice', axis=1)

    # Fit and transform training data
    pp = PreProcessor()
    X_train_pp = pp.fit_transform(X_train)
    train_pp = X_train_pp.assign(SalePrice=train['SalePrice'])

    # Save preprocessed data and fitted preprocessor
    db.save(train_pp, *db_config, 'processed_train')
    joblib.dump(pp, os.path.join(DIR, 'app/pickle/PreProcessor.pkl'))
