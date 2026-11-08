import { watchFile } from "node:fs";
import { exec } from "node:child_process";

const generateOpenapiTsFile = () =>
  exec(
    `npx openapi-typescript ${process.env.OPENAPI_JSON_PATH} -o ${process.env.OPENAPI_TS_PATH}`,
  );

generateOpenapiTsFile();

if (process.env.WATCH_FILES == "true") {
  watchFile(process.env.OPENAPI_JSON_PATH, generateOpenapiTsFile);
}
