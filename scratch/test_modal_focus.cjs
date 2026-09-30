// Verification test for AccessibleModal focus trapping, tab wrapping, and Escape closing logic

class MockElement {
  constructor(name, focusable = true, disabled = false) {
    this.name = name;
    this.focusable = focusable;
    this.disabled = disabled;
  }
  focus() {
    activeElement = this;
  }
}

class MockModal {
  constructor(elements) {
    this.elements = elements;
  }
  querySelectorAll() {
    return this.elements.filter(el => el.focusable && !el.disabled);
  }
  contains(target) {
    return this.elements.includes(target);
  }
}

let activeElement = null;

function createModalEnvironment() {
  const closeBtn = new MockElement('close-button');
  const nameInput = new MockElement('name-input');
  const emailInput = new MockElement('email-input');
  const cancelBtn = new MockElement('cancel-button');
  const submitBtn = new MockElement('submit-button');
  
  const modalElements = [closeBtn, nameInput, emailInput, cancelBtn, submitBtn];
  const modal = new MockModal(modalElements);
  
  let closed = false;
  const onClose = () => { closed = true; };
  const onCloseRef = { current: onClose };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onCloseRef.current();
      return;
    }

    if (e.key === 'Tab') {
      const focusables = modal.querySelectorAll();
      if (!focusables || focusables.length === 0) {
        e.preventDefault();
        return;
      }

      const firstEl = focusables[0];
      const lastEl = focusables[focusables.length - 1];

      if (e.shiftKey) {
        if (activeElement === firstEl || !modal.contains(activeElement)) {
          e.preventDefault();
          lastEl.focus();
        }
      } else {
        if (activeElement === lastEl || !modal.contains(activeElement)) {
          e.preventDefault();
          firstEl.focus();
        }
      }
    }
  };

  return {
    modal,
    elements: { closeBtn, nameInput, emailInput, cancelBtn, submitBtn },
    handleKeyDown,
    isClosed: () => closed
  };
}

console.log("=== RUNNING ACCESSIBLE MODAL FOCUS & KEYBOARD TESTS ===");

// Test 1: Initial focus setup
{
  const env = createModalEnvironment();
  const focusables = env.modal.querySelectorAll();
  focusables[0].focus();
  console.log(`Test 1: Initial element focused -> ${activeElement.name}`);
  if (activeElement.name !== 'close-button') throw new Error("Expected initial focus on first element");
  console.log(" PASS: Initial focus correctly set on first interactive element.");
}

// Test 2: Typing inside input does NOT close modal or steal focus
{
  const env = createModalEnvironment();
  env.elements.nameInput.focus();
  let defaultPrevented = false;
  const keyEvent = { key: 'a', shiftKey: false, preventDefault: () => { defaultPrevented = true; } };
  env.handleKeyDown(keyEvent);
  if (env.isClosed()) throw new Error("Modal should NOT close on typing key 'a'");
  if (defaultPrevented) throw new Error("Typing should NOT be prevented");
  if (activeElement.name !== 'name-input') throw new Error("Focus was stolen from input!");
  console.log(" PASS: Keystrokes inside input do not close modal or steal focus.");
}

// Test 3: Tab containment - Tab on last element wraps to first element
{
  const env = createModalEnvironment();
  env.elements.submitBtn.focus(); // Last element
  let defaultPrevented = false;
  const tabEvent = { key: 'Tab', shiftKey: false, preventDefault: () => { defaultPrevented = true; } };
  env.handleKeyDown(tabEvent);
  if (!defaultPrevented) throw new Error("Tab on last element must prevent default browser tabbing out of modal");
  if (activeElement.name !== 'close-button') throw new Error(`Expected focus to wrap to first element (close-button), got ${activeElement.name}`);
  console.log(" PASS: Forward Tab from last element wraps back to first element (Focus trapped inside modal).");
}

// Test 4: Shift+Tab containment - Shift+Tab on first element wraps to last element
{
  const env = createModalEnvironment();
  env.elements.closeBtn.focus(); // First element
  let defaultPrevented = false;
  const shiftTabEvent = { key: 'Tab', shiftKey: true, preventDefault: () => { defaultPrevented = true; } };
  env.handleKeyDown(shiftTabEvent);
  if (!defaultPrevented) throw new Error("Shift+Tab on first element must prevent default browser tabbing out of modal");
  if (activeElement.name !== 'submit-button') throw new Error(`Expected focus to wrap to last element (submit-button), got ${activeElement.name}`);
  console.log(" PASS: Shift+Tab from first element wraps back to last element (Reverse focus trapped inside modal).");
}

// Test 5: External focus containment - Tab when activeElement is outside modal pulls focus back inside
{
  const env = createModalEnvironment();
  const backgroundButton = new MockElement('background-page-btn');
  backgroundButton.focus();
  let defaultPrevented = false;
  const tabEvent = { key: 'Tab', shiftKey: false, preventDefault: () => { defaultPrevented = true; } };
  env.handleKeyDown(tabEvent);
  if (!defaultPrevented) throw new Error("Tab when outside modal must prevent default");
  if (activeElement.name !== 'close-button') throw new Error(`Expected focus pulled into modal, got ${activeElement.name}`);
  console.log(" PASS: Stray external focus immediately trapped back into modal.");
}

// Test 6: Escape key closes modal
{
  const env = createModalEnvironment();
  env.elements.nameInput.focus();
  let defaultPrevented = false;
  const escEvent = { key: 'Escape', preventDefault: () => { defaultPrevented = true; } };
  env.handleKeyDown(escEvent);
  if (!defaultPrevented) throw new Error("Escape key must call preventDefault");
  if (!env.isClosed()) throw new Error("Escape key must trigger modal onClose");
  console.log(" PASS: Escape key immediately dismisses modal dialog.");
}

console.log("\n=== ALL 6 MODAL FOCUS TRAP & ACCESSIBILITY TESTS PASSED! ===");
