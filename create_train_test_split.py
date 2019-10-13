#!/usr/bin/env python3
"""
A file for creating the train-test-validation split for the quranic text file.

Author: Hamzah Khan
Date: Jan. 23, 2019
"""

from argparse import ArgumentParser
import os

from sklearn.model_selection import train_test_split

import utils.text as text_utils

# This gives us a 60-20-20 split by default.
DEFAULT_RANDOM_SEED = 1
TRAIN_SPLIT_FRACTION = 0.6
TEST_SPLIT_FRACTION  = 0.2
VALIDATION_SPLIT_FRACTION = 0.2

parser = ArgumentParser(description='Tarteel Data Train-Test-Validation Splitter')
parser.add_argument('-f', '--path_to_quran_json', type=str, default="data/data-uthmani.json",
                    help="Path to the Qur'anic text Json file.")
parser.add_argument('-o', '--output_directory', type=str)
parser.add_argument('-d', '--dont_group_identical_text', action='store_true',
                    help="""If True, ayahs with identical text will be grouped into one set, not spread across
                            multiple sets.""")
parser.add_argument('--train_frac', type=float, default=TRAIN_SPLIT_FRACTION)
parser.add_argument('--test_frac', type=float, default=TEST_SPLIT_FRACTION)
parser.add_argument('--validation_frac', type=float, default=VALIDATION_SPLIT_FRACTION)
parser.add_argument('-s', '--seed', type=int, default=DEFAULT_RANDOM_SEED)
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

# Define constants.
NUM_SURAHS = 114


def create_train_test_validation_split(ayahs_to_text, train_test_validate_fractions, should_group_identical_text=True,
                                       random_seed=DEFAULT_RANDOM_SEED):
    """
    Create a train-test-validation split over ayahs with the same text, given the Qur'anic data.
    Returns a list of lists, each an ayah group, containing the ayah numbers.
    """
    train_frac = train_test_validate_fractions[0]
    test_frac = train_test_validate_fractions[1]
    validate_frac = train_test_validate_fractions[2]

    # The fractions should sum to 1.0, or we throw an error.
    if abs(sum(train_test_validate_fractions) - 1.0) > 1e-6:
        raise Exception("Train-test-validation fractions do not sum to 1.")

    # Initialize output.
    ayah_groups = []
    if should_group_identical_text:
        # Initialize text to ayah group dictionary.
        text_to_grouped_ayahs = {}

        # Cluster ayahs with the same text.
        for ayah_num in ayahs_to_text:
            ayah_text = ayahs_to_text[ayah_num]

            # Initialize if ayah text is not an entry yet.
            if ayah_text not in text_to_grouped_ayahs:
                text_to_grouped_ayahs[ayah_text] = []

            text_to_grouped_ayahs[ayah_text].append(ayah_num)

        # Get grouped list of ayahs.
        ayah_groups = list(text_to_grouped_ayahs.values())

    # If we want identical-text ayahs to not be grouped (and therefore allow the same text in multiple data sets), then
    # extract the ayah numbers.
    else:
        ayah_groups = [[ayah_num] for ayah_num in ayahs_to_text.keys()]

    # Splitting will be done in two steps, so identify the proper fractions for them.
    first_split_frac = train_frac + validate_frac
    second_split_frac = 1.0 - (validate_frac / first_split_frac)

    # Perform the actual splits on the indices.
    X_train_valid, X_test = train_test_split(range(len(ayah_groups)),
                                             train_size=first_split_frac,
                                             random_state=random_seed,
                                             shuffle=True)
    X_train, X_valid = train_test_split(X_train_valid,
                                        train_size=second_split_frac,
                                        random_state=random_seed,
                                        shuffle=True)

    # Convert the indices back into ayah groups.
    X_train = [ayah_groups[index] for index in X_train]
    X_test = [ayah_groups[index] for index in X_test]
    X_valid = [ayah_groups[index] for index in X_valid]

    return X_train, X_test, X_valid

def save_split_data(output_directory, filename, split_data):
    """
    Creates and saves a file for a specific split. Each line is a comma separated list of groups of ayah numbers.
    """
    output_path = os.path.join(output_directory, filename + ".txt")

    with open(output_path, "w+") as output_file:
        for ayah_group in split_data:
            # for ayah in ayah_group:
            output_file.write(str(ayah_group))
            output_file.write("\n")

        # Close the file after writing to it. 
        output_file.close()

def save_splits(output_directory, random_seed, split_fractions, X_train, X_test, X_valid):
    """
    Saves the train-test-validation splits to three files. 
    """
    # Create the filenames.
    train_filename = "_".join(["train", "fraction", str(split_fractions[0]), "seed", str(random_seed)])
    test_filename = "_".join(["test", "fraction", str(split_fractions[1]), "seed", str(random_seed)])
    validate_filename = "_".join(["validate", "fraction", str(split_fractions[2]), "seed", str(random_seed)])
    
    # Save the data to the specified location.
    save_split_data(output_directory, train_filename, X_train)
    save_split_data(output_directory, test_filename, X_test)
    save_split_data(output_directory, validate_filename, X_valid)


if __name__ == '__main__':
    # Load the Qur'anic Json data.
    quran_json_obj = text_utils.load_quran_obj_from_json(args.path_to_quran_json);

    # Convert the Json data to a dictionary of ayah numbers as keys and text as values.
    ayahs_to_text = text_utils.convert_quran_json_to_dict(quran_json_obj, should_include_bismillah=False)

    # Run the ayah split, forming groups of ayah numbers with identical text.
    split_fractions = [args.train_frac, args.test_frac, args.validation_frac]
    X_train, X_test, X_valid = create_train_test_validation_split(ayahs_to_text, split_fractions,
                                                                  not args.dont_group_identical_text, args.seed)

    # Save the resulting split to a file.
    if args.output_directory is not None:
        save_splits(args.output_directory, args.seed, split_fractions, X_train, X_test, X_valid)
        if args.verbose:
            print("Split data written to files in " + args.output_directory)
    else:
        if args.verbose:
            print("Data splitting completed.")
