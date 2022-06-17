#########################################################################
#                            Dusi's Thesis                              #
# Algorithmic Discrimination and Natural Language Processing Techniques #
#########################################################################

# This file contains the settings for the whole project, in a centralized place.

import torch

# PYTORCH COMPUTING

# Determinism
RANDOM_SEED: int = 42
torch.manual_seed(RANDOM_SEED)

# If available, torch computes on a parallel architecture
pt_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# FILES

# Folders structure
FOLDER_DATA = 'data'
FOLDER_RESULTS = 'results'
FOLDER_SAVED = 'saved'
FOLDER_SAVED_MODELS = FOLDER_SAVED + '/models'

# ENCODING

# Distribution models
DISTRIBUTION_GAUSSIAN_MIXTURE_MODEL_NAME: str = 'gmm'
DISTRIBUTION_SUPPORT_VECTOR_MACHINE_NAME: str = 'svm'
DEFAULT_DISTRIBUTION_MODEL_NAME: str = DISTRIBUTION_GAUSSIAN_MIXTURE_MODEL_NAME

# Model names and parameters
DEFAULT_BERT_MODEL_NAME: str = 'bert-base-uncased'

# Templates
TOKEN_CLS: str = '[CLS]'
TOKEN_SEP: str = '[SEP]'
TOKEN_MASK: str = '[MASK]'
DEFAULT_STANDARDIZED_EMBEDDING_TEMPLATE: str = TOKEN_CLS + " %s " + TOKEN_SEP
DEFAULT_STANDARDIZED_EMBEDDING_WORD_INDEX: int = 1

# PRINTING

# Printing things in tables
OUTPUT_TABLE_COL_SEPARATOR: str = '\t'
OUTPUT_TABLE_ARRAY_ELEM_SEPARATOR: str = ' '
OUTPUT_TABLE_FILE_EXTENSION: str = 'tsv'

# PLOTTING

# PyPlot colormaps
GENDER_CYAN2PINK_COLORMAP_NAME: str = 'cool'

OUTPUT_IMAGE_FILE_EXTENSION: str = 'png'
