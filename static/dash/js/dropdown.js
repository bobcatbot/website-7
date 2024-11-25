function Select(el, options={ placeholder: '', type: '', multiple: false, maxItems: 1, clearAll: false, removeBtn: false, Addall: false, options: [], disabled: false }) {
  const selectWrapper = document.querySelector(`${el}`);
  const select = selectWrapper.querySelector('.select');
  const selectSelected = select.querySelector('.select-selected');
  const selectOptions = select.querySelector('.select-options');
  const optionsList = selectOptions.querySelectorAll('.option');
  
  let selectedOptionsList = [];
  let selectedOptionsListVals = [];

  // Function to get the selected options
  this.getSelectedOptions = function() {
    return selectedOptionsList.map(item => item.id ?? item.value);
  };
  
  this.getSelectedOptionsIds = function() { // Deprecated
    return selectedOptionsListVals;
  };

  // Function to update and display selected options
  function updateSelectedOptions() {
    selectSelected.innerHTML = '';
    if (options.multiple && selectedOptionsList.length > 0) {
      selectedOptionsList.forEach(function(selectedOption) {
        const chip = document.createElement('div');
        chip.classList.add('chip');
        chip.setAttribute('data-type', options.type);
        chip.textContent = selectedOption.name ?? selectedOption.value;

        if (options.removeBtn) {
          const removeOption = document.createElement('span');
          removeOption.classList.add('remove-option');
          removeOption.textContent = 'X';
          removeOption.addEventListener('click', function(event) {
            event.stopPropagation();
            removeSelectedOption(selectedOption);
          });
          chip.appendChild(removeOption);
        }

        selectSelected.appendChild(chip);
      });
    } else {
      if (selectedOptionsList.length > 0) {
        selectSelected.classList.remove('val-placeholder');
        selectSelected.classList.add('chip');
        selectSelected.textContent = selectedOptionsList[0].name ?? selectedOptionsList[0].value;
        selectSelected.setAttribute('data-type', options.type);
      } else {
        selectSelected.classList.remove('chip');
        selectSelected.classList.add('val-placeholder');
        selectSelected.textContent = options.placeholder || 'Select an option';
      }
    }

    optionsList.forEach(function(option) {
      const isSelected = selectedOptionsList.some(selectedOption => 
        (selectedOption.id && selectedOption.id === option.dataset.id) ||
        (selectedOption.name && selectedOption.name === option.dataset.name) ||
        (selectedOption.value && selectedOption.value === option.dataset.value)
      );
      if (isSelected) {
        option.classList.add('selected');
      } else {
        option.classList.remove('selected');
      }
    });

    // Dispatch select:update event
    const updateEvent = new CustomEvent('select:update', {
      detail: {
        selectedOptions: selectedOptionsList.map(item => item.id ?? item.value),
        selectedOptionVals: selectedOptionsListVals,
      }
    });
    selectWrapper.dispatchEvent(updateEvent);
  }

  // Remove selected option
  function removeSelectedOption(option) {
    const index = selectedOptionsList.indexOf(option);
    if (index > -1) {
      selectedOptionsList.splice(index, 1);
      selectedOptionsListVals.splice(index, 1);
      updateSelectedOptions();
    }
  }

  // Clear all options
  function clearAllOptions() {
    selectedOptionsList.length = 0;
    updateSelectedOptions();
  }
  
  selectSelected.classList.add('placeholder');
  selectSelected.textContent = options.placeholder || 'Select an option';

  // Load default values if options parameter is not an empty array
  if (Array.isArray(options.options) && options.options.length > 0) {
    options.options.forEach(function(defaultOption) {
      const option = Array.from(optionsList).find(function(element) {
        return (element.dataset.id && element.dataset.id === defaultOption) ||
               (element.dataset.value && element.dataset.value === defaultOption);
      });
      if (option) {
        option.classList.add('selected');
        selectSelected.classList.remove('placeholder');
        
        const dictItem = { name: option.textContent, id: option.dataset.id, value: option.dataset.value };
        selectedOptionsList.push(dictItem);
      }
    });
    updateSelectedOptions();

    // Dispatch select:load event
    const loadEvent = new CustomEvent('select:load', {
      detail: {
        selectedOptions: selectedOptionsList.map(item => item.id ?? item.value),
        selectedOptionVals: selectedOptionsListVals,
      }
    });

    console.log('dispatching select:load event')
    selectWrapper.dispatchEvent(loadEvent);
  }
  
  optionsList.forEach(function(item) {
    item.addEventListener('click', function() {
      if (!options.multiple || !options.maxItems === 0) {
        selectedOptionsList.length = 0;
        selectedOptionsListVals.length = 0;
      }

      const optionItem = { name: item.textContent, id: item.dataset.id, value: item.dataset.value };
      if (!item.classList.contains('selected')) {
        if (options.maxItems === 0 || selectedOptionsList.length < options.maxItems) {
          selectedOptionsList.push(optionItem);
        }
      } else {
        removeSelectedOption(optionItem);
      }

      updateSelectedOptions();
    });
  });

  if (options.clearAll) {
    const clearAllButton = document.createElement('button');
    clearAllButton.textContent = 'X';
    clearAllButton.classList.add('clear-all-button');
    clearAllButton.addEventListener('click', function(event) {
      event.stopPropagation();
      clearAllOptions();
    });
    select.appendChild(clearAllButton);
  }

  if (!options.disabled) {
    select.addEventListener('click', function() {
      selectOptions.classList.add('active');
    });
  } else {
    select.setAttribute('disabled', 'true');
  }

  document.addEventListener('click', function(event) {
    if (!selectWrapper.contains(event.target)) {
      selectOptions.classList.remove('active');
    }
  });

  select.addEventListener('click', function(event) {
    if (!selectWrapper.contains(event.target)) {
      selectOptions.classList.remove('active');
    }
  });

  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      selectOptions.classList.remove('active');
    }
  });
}
