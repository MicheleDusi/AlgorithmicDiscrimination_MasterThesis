#########################################################################
#                            Dusi's Thesis                              #
# Algorithmic Discrimination and Natural Language Processing Techniques #
#########################################################################

# Using an SVM to predict gender from the embeddings

import math
import random

import numpy as np
from sklearn import svm
from datasets import Dataset, DatasetDict

from src.models.gender_enum import Gender
from src.models.templates import Template
from src.models.word_encoder import WordEncoder
from src.parsers.jneidel_occupations_parser import ONEWORD_OCCUPATIONS
import settings


EXPERIMENT_NAME: str = "embeddings_gender_classification"
FOLDER_OUTPUT: str = settings.FOLDER_RESULTS + "/" + EXPERIMENT_NAME
FOLDER_OUTPUT_IMAGES: str = FOLDER_OUTPUT + "/" + settings.FOLDER_IMAGES
FOLDER_OUTPUT_TABLES: str = FOLDER_OUTPUT + "/" + settings.FOLDER_TABLES

genders: list[Gender] = [
	Gender.MALE,
	Gender.FEMALE,
]

templates: list[Template] = [
	Template("[CLS] $NOM_PRONOUN is a %s [SEP]", target_index=4),
	Template("[CLS] $NOM_PRONOUN works as a %s [SEP]", target_index=5),
	Template("[CLS] $NOM_PRONOUN has a job as a %s [SEP]", target_index=7),
	Template("[CLS] $NOM_PRONOUN worked as a %s [SEP]", target_index=5),
	Template("[CLS] $NOM_PRONOUN will be a %s [SEP]", target_index=5),
	Template("[CLS] $NOM_PRONOUN could never become a %s [SEP]", target_index=6),
	Template("[CLS] $NOM_PRONOUN will be an amazing %s [SEP]", target_index=6),
	Template("[CLS] Being a %s is all $NOM_PRONOUN has ever wanted [SEP]", target_index=3),
	Template("[CLS] $NOM_PRONOUN will become a %s within a year [SEP]", target_index=5),
	Template("[CLS] $POSS_PRONOUN life dream is to become a %s [SEP]", target_index=8),
	Template("[CLS] $NOM_PRONOUN loves to be a %s [SEP]", target_index=6),
]


def sample_random_grid_indices(lengths: list[int] | tuple[int, ...], samples: int) -> list[np.ndarray]:
	max_combinations: int = math.prod(lengths)
	lengths: np.ndarray = np.asarray(lengths, dtype=np.uint32)
	increments: np.ndarray = np.ones(shape=lengths.shape, dtype=np.uint32)
	curr: np.ndarray = np.zeros(shape=lengths.shape, dtype=np.uint32)
	indices: list[np.ndarray] = []
	for i in range(min(samples, max_combinations)):
		indices.append(curr)
		curr = np.remainder(np.add(curr, increments), lengths)

	"""
	NOTE THAT THIS IS WRONG.
	Here's an example with lengths:
	[2, 3, 4, 5]
	
	This is the list of indices tuples generated by the method.
	[0 0 0 0]
	[1 1 1 1]
	[0 2 2 2]
	[1 0 3 3]
	[0 1 0 4]
	[1 2 1 0]
	[0 0 2 1]
	[1 1 3 2]
	[0 2 0 3]
	[1 0 1 4]
	[0 1 2 0]
	[1 2 3 1]
	[0 0 0 2]
	We can never have something with: 
	[0 _ 1 _]
	because GCD(2, 4) != 1
	"""
	return indices


def create_general_dataset(occupations: list[str], samples: int = "all") -> DatasetDict:
	encoder = WordEncoder(model=settings.DEFAULT_BERT_MODEL_NAME)
	data_occs: list[str] = []
	data_tmpl: list[str] = []
	data_gend: list[int] = []
	data_sntc: list[str] = []
	data_embs: list[np.ndarray] = []

	random.shuffle(occupations)
	lengths = [len(templates), len(genders), len(occupations)]
	if samples == "all":
		samples = int(np.prod(lengths))
	indices = sample_random_grid_indices(lengths=lengths, samples=samples)
	for index in indices:
		tmpl = templates[index[0]]
		gend = genders[index[1]]
		occ = occupations[index[2]]

		# Instancing template's sentence with pronouns
		instance_template = tmpl.sentence\
			.replace('$NOM_PRONOUN', gend.nom_pronoun)\
			.replace('$ACC_PRONOUN', gend.acc_pronoun)\
			.replace('$POSS_PRONOUN', gend.poss_pronoun)
		# Fixing template for the encoder
		encoder.set_embedding_template(template=instance_template, word_index=tmpl.target_index)
		embedding = encoder.embed_word_merged(occ, layers=[12]).detach().numpy()[0]
		data_occs.append(occ)
		data_tmpl.append(tmpl.sentence)
		data_gend.append(gend)
		data_sntc.append(instance_template % occ)
		data_embs.append(embedding)
	"""
	for tmpl in templates:
		print(f"\tTemplate: {tmpl.sentence}")
		for gend in genders:
			print(f"\t\tGender: {gend.name}")
			# Instancing template's sentence with pronouns
			instance_template = tmpl.sentence\
				.replace('$NOM_PRONOUN', gend.nom_pronoun)\
				.replace('$ACC_PRONOUN', gend.acc_pronoun)\
				.replace('$POSS_PRONOUN', gend.poss_pronoun)
			# Fixing template for the encoder
			encoder.set_embedding_template(template=instance_template, word_index=tmpl.target_index)

			for occ in occupations:
				# print(f"\t\t\tOccupation: {occ}")
				embedding = encoder.embed_word_merged(occ, layers=[12]).detach().numpy()[0]
				data_occs.append(occ)
				data_tmpl.append(tmpl.sentence)
				data_gend.append(gend)
				data_sntc.append(instance_template % occ)
				data_embs.append(embedding)
	"""
	# Creating dataset
	dataset: Dataset = Dataset.from_dict({
		"occupation": data_occs,
		"template": data_tmpl,
		"gender": data_gend,
		"sentence": data_sntc,
		"embedding": data_embs,
	})
	print(f"Created general dataset with {len(dataset)} rows.")
	if samples != "all":
		dataset = dataset.select(range(samples))
	dataset = dataset.shuffle(seed=settings.RANDOM_SEED)
	dataset_dict: DatasetDict = dataset.train_test_split(test_size=0.2)
	return dataset_dict


def launch_linear_svc_with_random_general_dataset(occupations: list[str]) -> None:
	"""
	This function launches the second experiment of this session.
	It takes the occupation list and, with a set of different templates, it creates an artificial dataset of multiple
	combinations over the two given genders: male and female.
	The resulting dataset is split in "training" and "testing".
	Finally, a Linear Support Vector Classifier is trained over the training dataset, and tested over the testing dataset.
	More than 96% of samples in the testing dataset are usually correctly gender-predicted.
	:param occupations: The list of occupations
	:return: None
	"""
	print("Creating dataset...", end='')
	dataset = create_general_dataset(occupations, samples=1000)
	train_dataset = dataset["train"]
	test_dataset = dataset["test"]
	print("Completed.")

	print("Training SVM...", end='')
	classifier = svm.LinearSVC()
	classifier.fit(train_dataset["embedding"], train_dataset["gender"])
	print("Completed.")

	print("Evaluating SVM...", end='')
	predicted = classifier.predict(test_dataset["embedding"])
	test_dataset = test_dataset.add_column("predicted_gender", predicted)
	test_errors = test_dataset.filter(lambda row: row["predicted_gender"] != row["gender"])
	print("Completed.")

	print(f"Length of the test dataset: {len(test_dataset)}")
	print(f"Gender prediction errors:   {len(test_errors)}")
	print(f"Accuracy:                   {100 - len(test_errors) / len(test_dataset) * 100:4.2f} %")
	for row in test_errors:
		print(f"Error (expected: {row['gender']}, predicted: {row['predicted_gender']}) in sentence \"{row['sentence']}\"")

	print("Analyzing the classifier coefficients.")
	print(f"Coefficients shape: {classifier.coef_.shape}")
	coefficients = classifier.coef_[0]      # Coefficients is now a 1D-ndarray of length (768)
	sample = test_dataset["embedding"][0]
	res = np.dot(coefficients, sample)
	print(f"Sentence: \"{test_dataset['sentence'][0]}\" - Score: {res}")

	return


def launch_linear_svc_with_split_dataset(occupations: list[str]) -> None:
	"""
	This function launches the first experiment of the session.
	It takes the occupation list and splits it in two: the training and the testing datasets.
	The occupations are instantiated in a single template, for both Male and Female gender pronouns.
	Then, a Linear Support Vector Classifier is trained over the training dataset, and tested over the testing dataset.
	More than 99% of samples in the testing dataset are correctly gender-predicted.

	:param occupations: The list of occupations
	:return: None
	"""
	# Shuffling
	random.shuffle(occupations)
	# Splitting the dataset in training (80%) and evaluation (20%)
	split_index = int(len(occupations) * 0.8)
	train_occs = occupations[:split_index]
	eval_occs = occupations[split_index:]

	# Preparing encoders
	encoder_m = WordEncoder(model=settings.DEFAULT_BERT_MODEL_NAME)
	encoder_f = WordEncoder(model=settings.DEFAULT_BERT_MODEL_NAME)
	encoder_m.set_embedding_template("[CLS] he works as a %s [SEP]", 5)
	encoder_f.set_embedding_template("[CLS] she works as a %s [SEP]", 5)

	def m_embed(word: str) -> np.ndarray:
		return encoder_m.embed_word_merged(word, layers=[12]).detach().numpy()[0]

	def f_embed(word: str) -> np.ndarray:
		return encoder_f.embed_word_merged(word, layers=[12]).detach().numpy()[0]

	# TRAINING
	print("Training SVM...", end='')
	train_xs = []
	train_ys = []
	for occ in train_occs:
		m_emb = m_embed(occ)
		f_emb = f_embed(occ)
		train_xs.extend([m_emb, f_emb])
		train_ys.extend([Gender.MALE, Gender.FEMALE])

	classifier = svm.LinearSVC()
	classifier.fit(train_xs, train_ys)
	print("Completed.")

	# EVALUATION
	print("Evaluating SVM...", end='')
	eval_xs = []
	eval_ys = []
	predicted_occs = []
	for occ in eval_occs:
		m_emb = m_embed(occ)
		f_emb = f_embed(occ)
		eval_xs.extend([m_emb, f_emb])
		eval_ys.extend([Gender.MALE, Gender.FEMALE])
		predicted_occs.extend(["[M] " + occ, "[F] " + occ])

	predicted_y = classifier.predict(eval_xs)
	print("Completed.")

	print("List of prediction errors:")
	n = 0
	for ey, py, occ in zip(eval_ys, predicted_y, predicted_occs):
		if ey == py:
			n += 1
		else:
			print(f"{occ:20s} Expected: {ey}\t\tPredicted: {py}")
	print()
	print(f"Totale:      {n}/{len(predicted_occs)}")
	print(f"Percentuale: {n / len(predicted_occs) * 100:5.3f}%")


def launch() -> None:
	"""
	Launches the experiments of this session.
	"""
	# Retrieving occupations list
	occupations_list = ONEWORD_OCCUPATIONS

	# First sub-experiment
	# launch_linear_svc_with_split_dataset(occupations=occupations_list)

	# Second sub-experiment
	launch_linear_svc_with_random_general_dataset(occupations=occupations_list)
	pass

