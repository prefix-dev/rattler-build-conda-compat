
from itertools import product
from typing import List, Mapping

def variant_combinations(data) -> List[Mapping[str, str]]:
    zip_keys = data.pop("zip_keys", [])
    # Separate the keys that need to be zipped from the rest
    zip_keys_flat = [item for sublist in zip_keys for item in sublist]
    other_keys = [key for key in data.keys() if key not in zip_keys_flat]

    # Create combinations for non-zipped keys
    other_combinations = list(product(*[data[key] for key in other_keys]))

    # Create zipped combinations
    zipped_combinations = [list(zip(*[data[key] for key in zip_group])) for zip_group in zip_keys]

    # Combine zipped combinations
    zipped_product = list(product(*zipped_combinations))

    # Combine all results into dictionaries
    final_combinations = []
    for other_combo in other_combinations:
        for zipped_combo in zipped_product:
            combined = {}
            # Add non-zipped items
            for key, value in zip(other_keys, other_combo):
                combined[key] = str(value)
            # Add zipped items
            for zip_group, zip_values in zip(zip_keys, zipped_combo):
                for key, value in zip(zip_group, zip_values):
                    combined[key] = str(value)
            final_combinations.append(combined)

    return final_combinations

