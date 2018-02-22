#!/usr/bin/env python
import os
os.environ['CONTENTWORKSHOP_URL']= 'http://127.0.0.1:8000'


import argparse
import json
import re
import shutil
import zipfile

from le_utils.constants import languages as languages
from le_utils.constants import format_presets, licenses, exercises

from ricecooker.chefs import SushiChef
from ricecooker.classes.nodes import ExerciseNode
from ricecooker.classes.questions import PerseusQuestion
from ricecooker.classes.licenses import get_license




LOCALPATH_REGEX = re.compile(r'\$\{☣ LOCALPATH\}/')  # .persus image links start with this
BASE_EXERCISE_STORAGE = 'chefdata/unzippedperseus'


class LocalPerseusExercise(object):
    """
    Helper class to handle unzipping and parsing zipped .perseus exercises.
    """

    def __init__(self, perseus_src_path):
        basename = os.path.basename(perseus_src_path)
        perseus_name, ext = os.path.splitext(basename)
        assert ext in ['.zip', '.perseus']
        self.perseus_name = perseus_name
        if not os.path.exists(BASE_EXERCISE_STORAGE):
            os.makedirs(BASE_EXERCISE_STORAGE, exist_ok=True)
        self.unzipped_dir = os.path.join(BASE_EXERCISE_STORAGE, perseus_name)
        self.unzip_tmp(perseus_src_path)
        self.replace_RADIOACTIVE_LOCALPATH()

    def unzip_tmp(self, perseus_src_path):
        self.delete_tmp()
        zip_ref = zipfile.ZipFile(perseus_src_path, 'r')
        zip_ref.extractall(self.unzipped_dir)
        zip_ref.close()
        
    def delete_tmp(self):
        if os.path.exists(self.unzipped_dir):
            shutil.rmtree(self.unzipped_dir)

    def replace_RADIOACTIVE_LOCALPATH(self):
        """
        Transform every occurence in text of the pattern:
        ${☣ LOCALPATH}/  -->  chefdata/unzippedperseus/{perseus_name}/
        """
        EXCLUDE_JSONS = ['exercise.json']
        for filename in os.listdir(self.unzipped_dir):
            if filename.endswith('.json') and filename not in EXCLUDE_JSONS:
                json_file_path = os.path.join(self.unzipped_dir, filename)
                print('processing ', json_file_path)
                with open(json_file_path, 'r') as inf:
                    intext = inf.read()
                outtext = LOCALPATH_REGEX.sub(self.unzipped_dir+'/', intext)
                with open(json_file_path, 'w') as outf:
                    outf.write(outtext)

    def get_exercise_data(self):
        exercise_json_path = os.path.join(self.unzipped_dir, 'exercise.json')
        with open(exercise_json_path) as infile:
            exercise_data = json.load(infile)
        return exercise_data

    def get_question_paths(self):
        exercise_data = self.get_exercise_data()
        question_paths = {}
        for question_id, question_type in exercise_data['assessment_mapping'].items():
            if question_type == 'perseus_question':
                question_path = os.path.join(self.unzipped_dir, question_id + '.json')
                question_paths[question_id] = question_path
        # verification is the highest form of trust
        for question_path in question_paths.values():
            assert os.path.exists(question_path)
        return question_paths





class PerseusChef(SushiChef):
    """
    This is simple sushi chef to test the new ePub files work inside DocumentNodes.
    """
    channel_info = {
        'CHANNEL_SOURCE_DOMAIN': 'learningequality.org',       # make sure to change this when testing
        'CHANNEL_SOURCE_ID': 'perseus_tester',   # channel's unique id
        'CHANNEL_TITLE': 'Perseus exercises test channel',
        'CHANNEL_LANGUAGE': 'en',
        'CHANNEL_THUMBNAIL': None,
        'CHANNEL_DESCRIPTION': 'This is a test channel with a single perseus exercise in it.'
    }

    def __init__(self, *args, **kwargs):
        super(PerseusChef, self).__init__(*args, **kwargs)

        # We don't want to add argparse help if subclass has an __init__ method
        self.arg_parser = argparse.ArgumentParser(
            description="Upload a .persues file to studio instance at http://127.0.0.1:8000",
            add_help=True, parents=[self.arg_parser]
        )
        self.arg_parser.add_argument('--perseusfile', required=True,
            action='store', help='Local path to the perseus source file.')

    def construct_channel(self, **kwargs):
        # create channel
        channel = self.get_channel(**kwargs)

        perseus_src_path = kwargs['perseusfile']
        lpe = LocalPerseusExercise(perseus_src_path)
        exercise_data = lpe.get_exercise_data()
        exercise = ExerciseNode(
                source_id=lpe.perseus_name,
                title='Local perseus exercise ' + lpe.perseus_name,
                author='LE content team',
                description='A sample exercise with Persus questions',
                language=languages.getlang('en').id,
                license=get_license(licenses.CC_BY, copyright_holder='Copyright holder name'),
                thumbnail=None,
                exercise_data={
                    'mastery_model': exercises.M_OF_N,         # or exercises.DO_ALL
                    'randomize': exercise_data['randomize'],
                    'm': exercise_data['m'],
                    'n': exercise_data['n'],
                },
                questions=[]
        )
        channel.add_child(exercise)
        
        for question_id, question_path in lpe.get_question_paths().items():
            # LOAD JSON DATA (as string) FOR PERSEUS QUESTIONS
            json_str = open(question_path, 'r').read()
            pq = PerseusQuestion(
                id=question_id,
                raw_data=json_str,
                source_url='file://[WHEREVERCHEFISRUNNING]'+question_path,
            )
            exercise.add_question(pq)
    
        return channel


if __name__ == '__main__':
    mychef = PerseusChef()
    mychef.main()
