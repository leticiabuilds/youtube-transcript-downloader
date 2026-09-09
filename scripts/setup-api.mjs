import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiDir = join(rootDir, "apps", "api");
const venvPython = join(apiDir, ".venv", "bin", "python");

function run(command, args, cwd) {
  const result = spawnSync(command, args, {
    cwd,
    stdio: "inherit",
    env: process.env,
  });

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

if (!existsSync(join(apiDir, "requirements.txt"))) {
  console.error("Could not find apps/api/requirements.txt");
  process.exit(1);
}

if (!existsSync(venvPython)) {
  console.log("Creating Python virtualenv in apps/api/.venv ...");
  run("python3", ["-m", "venv", ".venv"], apiDir);
}

console.log("Installing API Python dependencies ...");
run(venvPython, ["-m", "pip", "install", "-r", "requirements.txt"], apiDir);
console.log("API setup complete.");
