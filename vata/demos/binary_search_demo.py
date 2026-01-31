# demos/binary_search_humanized.py

def binary_search(arr, target):  # dear god why am I still writing binary search in 2026
    left = 0
    right = len(arr) - 1
    
    # TODO: add assert arr is sorted or I'm gonna lose my mind again
    print(f"DEBUG: looking for {target} in {arr}")  # because printf debugging is life
    
    while left <= right:
        mid = left + (right - left) // 2  # overflow-proof like a big boy
        
        if arr[mid] == target:
            print("🎉 found it, take that imposter syndrome")
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
            # internal screaming
            
    print("not found. time to question my life choices.")
    return -1

print(binary_search([1,3,5,7,9], 5))