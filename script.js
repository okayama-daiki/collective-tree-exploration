let pyodide;
let result;
let currentStep;
let isDisplayRobotLabels = false;

async function init() {
  pyodide = await loadPyodide();
  const file = await fetch("./src/collective_tree_exploration.py");
  const code = await file.text();
  await pyodide.runPythonAsync(code);
  const spinnerElement = document.querySelector(".spinner-container");
  spinnerElement.classList.add("hidden");
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
      case "ArrowDown":
      case "ArrowRight":
        next();
        break;
      case "ArrowUp":
      case "ArrowLeft":
        prev();
        break;
      default:
        break;
    }
  };
  await renderTree();
}

function makeDot(step) {
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
                    ? `{${result.steps[step].robotsInNode[node]}}`
                    : result.steps[step].robotsInNode[node].length
                }",
                  fontsize=10,
                  color="${
                    result.steps[step].traversed[node]
                      ? { 1: "green", 2: "red", 3: "blue" }[
                          result.steps[step].nodeCase[node]
                        ]
                      : "black"
                  }",
                  style="${
                    result.steps[step].traversed[node] ? "solid" : "dashed"
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
  const element = await viz.renderSVGElement(makeDot(currentStep));
  const treeContainer = document.querySelector(".tree-container");
  treeContainer.innerHTML = "";
  treeContainer.appendChild(element);

  const stepElement = document.querySelector(".step");
  stepElement.innerHTML = String(currentStep + 1);
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

async function downloadSVG() {
  const viz = new Viz();
  const svg = await viz.renderSVGElement(makeDot(currentStep));
  const svgString = new XMLSerializer().serializeToString(svg);
  const blob = new Blob([svgString], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "tree.svg";
  link.click();
}

async function downloadAllSVG() {
  const viz = new Viz();
  const svgString = await Promise.all(
    result.steps.map(async (step, index) => {
      const svg = await viz.renderSVGElement(makeDot(index));
      return new XMLSerializer().serializeToString(svg);
    })
  );
  const zip = new JSZip();
  svgString.forEach((svg, index) => {
    zip.file(`step-${index + 1}.svg`, svg);
  });
  const content = await zip.generateAsync({ type: "blob" });
  saveAs(content, "tree.zip");
}

async function toggleRobotLabels() {
  isDisplayRobotLabels = !isDisplayRobotLabels;
  await renderTree();
}

init();
