def snv(input_data):
    # Define a new array and populate it with the corrected data
    output_data = np.zeros_like(input_data)
    for i in range(input_data.shape[0]):
        # Apply correction
        output_data[i, :] = (input_data[i, :] - np.mean(input_data[i, :])) / np.std(
            input_data[i, :]
        )

    return output_data
