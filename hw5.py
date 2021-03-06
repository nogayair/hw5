import pathlib
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
from typing import Union, Tuple
import re

class QuestionnaireAnalysis:
    """
    Reads and analyzes data generated by the questionnaire experiment.
    Should be able to accept strings and pathlib.Path objects.
    """

    def __init__(self, data_fname: Union[pathlib.Path, str]):
        if pathlib.Path(data_fname).is_file():
            self.data_fname=pathlib.Path(data_fname)
        else:
            raise ValueError

    def read_data(self):
        """Reads the json data located in self.data_fname into memory, to
        the attribute self.data.
        """
        self.data = pd.read_json(self.data_fname)

    def show_age_distrib(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates and plots the age distribution of the participants.
        	Returns
            -------
            hist : np.ndarray
            Number of people in a given bin
            bins : np.ndarray
            Bin edges
                """
        bins = np.linspace(0,100,11)
        hist=np.histogram(self.data['age'], bins = bins)
        return hist

    def remove_rows_without_mail(self) -> pd.DataFrame:
        """Checks self.data for rows with invalid emails, and removes them.
        Returns
        ------
	    df : pd.DataFrame
	    A corrected DataFrame, i.e. the same table but with the erroneous rows removed and  
	    the (ordinal) index after a reset.
        """
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{1,6}$'
        return self.data[self.data['email'].str.contains(regex)].reset_index()

    def fill_na_with_mean(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Finds, in the original DataFrame, the subjects that didn't answer
        all questions, and replaces that missing value with the mean of the
        other grades for that student.

	Returns
	-------
	df : pd.DataFrame
	  The corrected DataFrame after insertion of the mean grade
	arr : np.ndarray
          Row indices of the students that their new grades were generated
        """
        grades = self.data.loc[:,'q1':'q5']
        na_index = np.where(grades.isna().any(axis=1))
        grades = grades.T.fillna(grades.mean(axis=1)).T
        self.data.loc[:,'q1':'q5'] = grades
        return self.data, na_index[0]


    def score_subjects(self, maximal_nans_per_sub: int = 1) -> pd.DataFrame:
        """Calculates the average score of a subject and adds a new "score" column
        with it.

        If the subject has more than "maximal_nans_per_sub" NaN in his grades, the
        score should be NA. Otherwise, the score is simply the mean of the other grades.
        The datatype of score is UInt8, and the floating point raw numbers should be
        rounded down.

        Parameters
        ----------
        maximal_nans_per_sub : int, optional
            Number of allowed NaNs per subject before giving a NA score.

        Returns
        -------
        pd.DataFrame
            A new DF with a new column - "score".
        """
        df=self.data
        grades = df.loc[:,'q1':'q5']
        self.maximal_nans_per_sub=maximal_nans_per_sub
        na_index = np.where(grades.isnull().sum(axis=1)>maximal_nans_per_sub)
        df['score']=grades.mean(numeric_only=True, axis=1).apply(np.floor)
        df['score'].loc[na_index]=np.nan
        df['score'] = pd.Series(df.score.values, dtype="UInt8")
        return df

    def correlate_gender_age(self) -> pd.DataFrame:
        """Looks for a correlation between the gender of the subject, their age
        and the score for all five questions.

        Returns
        -------
        pd.DataFrame
        A DataFrame with a MultiIndex containing the gender and whether the subject is above
        40 years of age, and the average score in each of the five questions.
        """
        df=self.data
        index_df = df.set_index([df.index, 'age', 'gender']) #a
        grouped=index_df.groupby([None, lambda age: age>40], level=['gender','age']).mean().loc[:,'q1':'q5']
        return grouped