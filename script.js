const COLOR_MAP = {
  FINISHED: "green",
  UNFINISHED: "red",
  INHABITED: "blue",
};

let pyodide;
let result;
let currentStep = 0;
let isDisplayRobotLabels = true;

async function init() {
  pyodide = await loadPyodide();
  const file = await fetch("./src/collective_tree_exploration.py");
  const code = await file.text();
  await pyodide.runPythonAsync(code);
  console.log("Pyodide is ready!");
}

async function run() {
  if (pyodide === undefined) return;
  const n = document.querySelector("input[name=n]").value;
  const k = document.querySelector("input[name=k]").value;
  const s = document.querySelector("input[name=s]").value;
  result = await pyodide.runPythonAsync(`run(${n}, ${k}, ${s})`);
  result = JSON.parse(result);
  currentStep = 0;
  const resultContainer = document.querySelector(".visualization-result");
  resultContainer.classList.remove("hidden");
  document.onkeydown = function (e) {
    switch (e.key) {
      case "ArrowRight":
        next();
        break;
      case "ArrowLeft":
        prev();
        break;
      default:
        break;
    }
  };
  await renderTree();
}

function makeDot() {
  const dot = `graph {
          graph []
          node [shape=circle];
          ${Array(result.tree.n)
            .fill(0)
            .map(
              (_, node) =>
                `${node} [
                  label="${node}\nrobots: ${
                  isDisplayRobotLabels
                    ? result.steps[currentStep].robotCount[node]
                    : result.steps[currentStep].nodeRobots[node]
                }",
                  fontsize=10,
                  color="${
                    COLOR_MAP[result.steps[currentStep].nodeStatus[node]]
                  }",
                  style="${
                    result.steps[currentStep].traversed[node]
                      ? "solid"
                      : "dotted"
                  }"
                ];`
            )
            .join("\n")}
          ${result.tree.edges
            .map((node) => `${node[0]} -- ${node[1]};`)
            .join("\n")}
        }`;
  return dot;
}

async function renderTree() {
  const viz = new Viz();
  const element = await viz.renderSVGElement(makeDot());
  const treeContainer = document.querySelector(".tree-container");
  treeContainer.innerHTML = "";
  treeContainer.appendChild(element);

  const stepElement = document.querySelector(".step");
  stepElement.innerHTML = `Step: ${currentStep + 1}`;
}

async function next() {
  if (result === undefined) return;
  if (currentStep < result.steps.length - 1) {
    currentStep++;
    await renderTree();
  } else {
    alert("Exploration is finished!");
  }
}

async function prev() {
  if (result === undefined) return;
  if (currentStep > 0) {
    currentStep--;
    await renderTree();
  } else {
    alert("This is the first step!");
  }
}

async function toggleRobotLabels() {
  isDisplayRobotLabels = !isDisplayRobotLabels;
  await renderTree();
}

init();
