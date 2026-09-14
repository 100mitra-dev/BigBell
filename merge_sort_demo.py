def merge_sort(arr: list[int]) -> list[int]:
    """Sorts a list of integers using merge sort algorithm.

    Parameters
    ----------
    arr: list[int]
        The list to sort.

    Returns
    -------
    list[int]
        A new sorted list.
    """
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    # Merge the sorted halves
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    # Append remaining items
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged

if __name__ == "__main__":
    test_data = [6, 4, 46, 888, 4, 1, 3]
    sorted_data = merge_sort(test_data)
    print("Input:", test_data)
    print("Sorted:", sorted_data)
