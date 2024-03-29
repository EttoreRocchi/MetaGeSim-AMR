"""
	This script defines some functions which test if the functions
	defined in input_file_preparation.py and in populationdistribution.py
	work properly
"""

__author__ = "Ettore Rocchi"

import pytest
import csv
import math
import numpy as np
import pathlib
from configparser import ConfigParser
from scripts.PopulationDistribution.populationdistribution import PopulationDistribution
from scripts.InputFilePreparation.input_file_preparation import *
from scripts.StrainSelector.strainselector import NoveltyCategory, StrainSelector
from scripts.MetaDataTable.metadatatable import MetadataTable


     #######################
     #    Preliminaries    #
     #######################

tsv_path = "./input_population/input.tsv"
json_path = "./input_population/input.json"

config_path = "./input_population/config.ini"
abundance_path = "./input_population/abundance.tsv"
metadata_path = "./input_population/metadata.tsv"
genome_to_id_path = "./input_population/genome_to_id.tsv"
simulation_dir = "./input_population"
genomes_info_path = "./input_population/genomes_info.json"

def is_float(string):
	"""
		This function is used to check if a given string is a float or not
	"""
	try:
		float(string)
		return True
	except ValueError:
		return False

def is_integer(string):
	"""
		This function is used to test if a given string is an integer or not
	"""
	try:
		int(string)
		return True
	except ValueError:
		return False

def is_bool(string):
	"""
		This function is used to test if a given string is a boolean or not
	"""
	try:
		bool(string)
		return True
	except ValueError:
		return False


     #######################
     #        Tests        #
     #######################

def test_Broken_stick_model_distributes_abundance_properly_input_genome_to_zero():
	"""
		This function tests if the sum of the relative abundances of the strain of a certain
		genome equals the original genome's abundance, given in input. This allows to test
		the correct functioning of the Broken stick model function when the abundance of the
		original genome is required to be zero at the end (input_genomes_to_zero = True)

		In order to avoid issues related to floating points and to approximations, the
		math.isclose() method is used
	"""

	genome_ID = 'First_genome'
	total_genomes_dict = {'First_genome': 0.7, 'Second_genome': 0.3, 'simulated_First_genome.Taxon001': 0, 'simulated_First_genome.Taxon002': 0}
	original_genome_abundance = total_genomes_dict[genome_ID]
	number_strains = 2
	original_dict = total_genomes_dict.copy()

	input_genomes_to_zero = True
	dict = PopulationDistribution.Broken_stick_model(genome_ID, total_genomes_dict, original_genome_abundance, number_strains, input_genomes_to_zero)

	assert math.isclose(dict['simulated_First_genome.Taxon001'] + dict['simulated_First_genome.Taxon002'], original_dict['First_genome'], abs_tol = 0.00001)


def test_Broken_stick_model_distributes_abundance_properly():
	"""
		This function tests if the sum between the relative abundances of the strain of a certain
		genome and the relative abundance of that genome equals the original genome's abundance,
		given in input. This allows to test the correct functioning of the Broken stick model
		function when the abundance of the original genome is not required to be zero at the end
		(input_genomes_to_zero = False)

		In order to avoid issues related to floating points and to approximations, the
		math.isclose() method is used
	"""

	genome_ID = 'First_genome'
	total_genomes_dict = {'First_genome': 0.7, 'Second_genome': 0.3, 'simulated_First_genome.Taxon001': 0, 'simulated_First_genome.Taxon002': 0}
	original_genome_abundance = total_genomes_dict[genome_ID]
	number_strains = 2
	original_dict = total_genomes_dict.copy()

	input_genomes_to_zero = False
	dict = PopulationDistribution.Broken_stick_model(genome_ID, total_genomes_dict, original_genome_abundance, number_strains, input_genomes_to_zero)

	assert math.isclose(dict['simulated_First_genome.Taxon001'] + dict['simulated_First_genome.Taxon002'] + dict['First_genome'], original_dict['First_genome'], abs_tol = 0.00001)


def test_abundances_input_equal_to_distributed_abundances():
	"""
		This function tests if the sum of the relative abundances given in input is equal
		to the sum of the output relative abundances (once they were re-distributed among
		the strains).

		In order to avoid issues related to floating points and to approximations, the
		math.isclose() method is used
	"""

	total_genomes_dict = {'E.coli': 0.5, 'S.aureus': 0.3, 'S.pneumoniae': 0.2, 'simulated_E.coli.Taxon001': 0, 'simulated_S.aureus.Taxon002': 0, 'simulated_S.pneumoniae.Taxon003': 0}
	total_abundances_input = sum(total_genomes_dict[key] for key in total_genomes_dict)

	np.random.seed(42)
	number_of_samples = np.random.randint(1, 10)
	population_list = [[0.0] * number_of_samples for _ in range(len(total_genomes_dict))]
	list_of_genome_id = [key for key in total_genomes_dict]
	input_genomes_to_zero = bool(np.random.randint(0, 2))

	dict_of_tsv_columns = read_and_store_tsv_input(tsv_path)
	wrt_abundance_file(abundance_path, dict_of_tsv_columns)

	distribution = PopulationDistribution()
	distribution.distribute_abundance_to_strains(population_list, number_of_samples, abundance_path, list_of_genome_id, input_genomes_to_zero)

	abundance_file = pathlib.Path(abundance_path)
	abundance_file.unlink()

	distributed_abundances = [0 for _ in range(number_of_samples)]
	for i in range(number_of_samples):
		for j in range(len(total_genomes_dict)):
			distributed_abundances[i] += population_list[j][i]
		assert math.isclose(total_abundances_input, distributed_abundances[i], abs_tol = 0.00001)


def test_genomes_total_greater_or_equal_to_input_genomes():
	"""
		This function tests if the number of input genomes is smaller than
		(or equal to) the number of genomes required at the end of the simulation
		(i.e number of input genomes + number of simulated strains)
	"""

	dict = read_and_store_tsv_input(tsv_path)

	with open(tsv_path, 'r') as tsv_file:
		tsv_reader = csv.reader(tsv_file, delimiter = '\t')
		next(tsv_reader, None)
		num_rows = sum(1 for row in tsv_reader)

	with open(json_path, 'r') as json_file:
		json_dict = json.load(json_file)

	total_num_genomes = int(json_dict['genomes_total'])

	assert  total_num_genomes >= num_rows


def test_tsv_rows_have_same_number_of_elements():
	"""
		This function tests if the input.tsv file is properly written, with
		each row having the expected number of elements
	"""

	dict_length = len(read_and_store_tsv_input(tsv_path))

	with open(tsv_path, 'r') as tsv_file:
		for row in csv.reader(tsv_file, delimiter = '\t'):
			assert len(row) == dict_length


def test_all_configs_are_set():
	"""
		This function tests if the config.ini file's options are set.
		The only parameter which may be empty is id_to_gff_file, since it
		is not necessary, in the known_distribution modality, to provide
		a gene annotation file
	"""

	config = ConfigParser()
	configuration_file_definition(config)

	tsv_dict = read_and_store_tsv_input(tsv_path)
	json_dict = read_and_store_json_input(json_path)

	configuration_file_settings(config, json_dict, tsv_dict, abundance_path, metadata_path, genome_to_id_path, simulation_dir)

	for section in config.sections():
		for key, value in config.items(section):
			if not key == 'id_to_gff_file':
				assert value != ''


def test_tsv_values_have_correct_types():
	"""
		This function tests if the input.tsv file is filled with values
		of the expected type. The functions is_float and is_integer are
		used to check this; they are defined at the beginning of the script
	"""

	tsv_dict = read_and_store_tsv_input(tsv_path)

	for key in tsv_dict:
		assert isinstance(tsv_dict[key], list)

	for i in range(len(tsv_dict['genome_IDs'])):
		assert isinstance(tsv_dict['genome_IDs'][i], str)
		assert tsv_dict['genome_IDs'][i] != ''
		assert isinstance(tsv_dict['species'][i], str)
		assert tsv_dict['species'][i] != ''
		assert is_float(tsv_dict['abundances'][i])
		assert (float(tsv_dict['abundances'][i]) <= 1 and float(tsv_dict['abundances'][i]) >= 0)
		assert is_float(tsv_dict['patric_IDs'][i])
		assert isinstance(tsv_dict['antibiotics'][i], str)
		assert tsv_dict['phenotypes'][i] in ["Resistant", "resistant", "Susceptible", "susceptible", "Intermediate", "intermediate"]
		assert is_integer(tsv_dict['genome_lengths'][i])
		assert tsv_dict['novelty_cats'][i] in ["known_strain", "known_genus", "known_family"] #attention!
		assert isinstance(tsv_dict['genome_filenames'][i], str)


def test_json_values_have_correct_types():
	"""
		This function tests if the input.json file's options are set to
		value of the expected type. The functions is_float, is_integer and
		is_bool are used to check this; they are defined at the beginning
		of the script
	"""

	json_dict = read_and_store_json_input(json_path)

	for key in json_dict:
		assert json_dict[key] != ""

	assert is_integer(json_dict["seed"])
	assert is_integer(json_dict["max_processor"])
	assert int(json_dict["max_processor"]) > 0
	assert is_float(json_dict["size"])
	assert is_integer(json_dict["fragm_size_mean"])
	assert is_integer(json_dict["fragm_size_std_dev"])
	assert is_integer(json_dict["number_of_samples"])
	assert int(json_dict["number_of_samples"]) > 0
	assert is_bool(json_dict["equally_distributed_strains"])
	assert is_bool(json_dict["input_genomes_to_zero"])
	assert is_integer(json_dict["genomes_total"])
	assert int(json_dict["genomes_total"]) > 0


def test_Broken_stick_model_strain_zero():
	"""
		This function tests the Broken stick model function to ensure it returns
		the original genome's abundance value when no strains for that genome is
		feneerated by sgEvolver
	"""

	genome_ID = 'Second_genome'
	total_genomes_dict = {'First_genome': 0.7, 'Second_genome': 0.3, 'simulated_First_genome.Taxon001': 0, 'simulated_First_genome.Taxon002': 0}
	original_genome_abundance = total_genomes_dict[genome_ID]
	number_strains = 0
	original_dict = total_genomes_dict.copy()

	np.random.seed(42)
	input_genomes_to_zero = bool(np.random.randint(0, 2))
	dict = PopulationDistribution.Broken_stick_model(genome_ID, total_genomes_dict, original_genome_abundance, number_strains, input_genomes_to_zero)

	assert dict['Second_genome'] == original_dict['Second_genome']


def test_draw_strains_works_properly_for_new_modality():
	"""
		This function tests if the modified version of the drawn_strains functions
		works properly in the new known_distribution modality; in this case we
		expect the output of get_drawn_genome_id to be a list of ordered genomes, where
		the other will reflect the order given in the input.tsv file
	"""

	dict_of_tsv_columns = read_and_store_tsv_input(tsv_path)
	wrt_metadata_file(metadata_path, dict_of_tsv_columns)

	metadata_table = MetadataTable()
	metadata_table.read(metadata_path, column_names=True)

	strainselector_obj = StrainSelector()
	number_of_genomes = 3
	limit_per_otu = 1
	select_random_genomes = False
	drawn_strains_list = strainselector_obj.get_drawn_genome_id(metadata_table, number_of_genomes, limit_per_otu, select_random_genomes)

	metadata_file = pathlib.Path(metadata_path)
	metadata_file.unlink()

	assert len(drawn_strains_list) == len(dict_of_tsv_columns['genome_IDs'])
	assert drawn_strains_list[0] == dict_of_tsv_columns['genome_IDs'][0]
	assert drawn_strains_list[1] == dict_of_tsv_columns['genome_IDs'][1]
	assert drawn_strains_list[2] == dict_of_tsv_columns['genome_IDs'][2]


def test_abundance_file_rows():
	"""
		This function tests if the abundance.tsv file has the expected number
		of rows (genomes), and the correct amount of columns (i.e. 2, one for
		the genome ID, one for the relative abundance)
	"""

	dict_of_tsv_columns = read_and_store_tsv_input(tsv_path)
	wrt_abundance_file(abundance_path, dict_of_tsv_columns)

	rows_num = 0
	with open (abundance_path, 'r') as abundance:
		for row in csv.reader(abundance, delimiter = '\t'):
			assert len(row) == 2
			rows_num += 1
		assert rows_num == len(dict_of_tsv_columns['genome_IDs'])
		assert rows_num == len(dict_of_tsv_columns['abundances'])

	abundance_file = pathlib.Path(abundance_path)
	abundance_file.unlink()


def test_metatada_file_rows():
	"""
		This function tests if the metadata.tsv file has the expected number
		of rows (number of genomes + 1), and the correct amount of columns
		(i.e. 4, one for the genome ID, one for the OTU, one for the NCBI ID,
		one for the novelty category)
	"""

	dict_of_tsv_columns = read_and_store_tsv_input(tsv_path)
	wrt_metadata_file(metadata_path, dict_of_tsv_columns)

	rows_num = 0
	with open (metadata_path, 'r') as metadata:
		for row in csv.reader(metadata, delimiter = '\t'):
			assert len(row) == 4
			rows_num += 1
		assert rows_num == len(dict_of_tsv_columns['genome_IDs']) + 1
		assert rows_num == len(dict_of_tsv_columns['patric_IDs']) + 1
		assert rows_num == len(dict_of_tsv_columns['novelty_cats']) + 1

	metadata_file = pathlib.Path(metadata_path)
	metadata_file.unlink()


def test_genome_to_id_file_rows():
	"""
		This function tests if the genome_to_id.tsv file has the expected number
		of rows (genomes), and the correct amount of columns (i.e. 2, one for the
		genome ID, one for the genome's file name)
	"""

	dict_of_tsv_columns = read_and_store_tsv_input(tsv_path)
	wrt_genome_to_id_file(genome_to_id_path, dict_of_tsv_columns, simulation_dir)

	rows_num = 0
	with open (genome_to_id_path, 'r') as genome_to_id:
		for row in csv.reader(genome_to_id, delimiter = '\t'):
			assert len(row) == 2
			rows_num += 1
		assert rows_num == len(dict_of_tsv_columns['genome_IDs'])
		assert rows_num == len(dict_of_tsv_columns['genome_filenames'])

	genome_to_id_file = pathlib.Path(genome_to_id_path)
	genome_to_id_file.unlink()


def test_genomes_info_file_keys():
	"""
		This function tests if the genomes_info.json file has the expected number
		of genomes, and each genome has the expected numbers of keys
	"""

	dict_of_tsv_columns = read_and_store_tsv_input(tsv_path)
	wrt_genomes_info_file(genomes_info_path, dict_of_tsv_columns, tsv_path)

	with open (genomes_info_path, 'r') as genomes_info:
		genomes_info_to_dict = json.load(genomes_info)

	assert len(genomes_info_to_dict) == len(dict_of_tsv_columns['genome_IDs'])
	for key in genomes_info_to_dict:
		assert len(genomes_info_to_dict[key]) == 7

	genomes_info_file = pathlib.Path(genomes_info_path)
	genomes_info_file.unlink()
