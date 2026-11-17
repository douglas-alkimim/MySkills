import assert from "node:assert/strict";
import { isMediaCapacityMessage } from "../dist/tools/handlers.js";

assert.equal(
  isMediaCapacityMessage("I'm sorry, I'm experiencing unusually high traffic and am at full capacity."),
  true
);
assert.equal(isMediaCapacityMessage("Tente novamente mais tarde; capacidade esgotada."), true);
assert.equal(isMediaCapacityMessage("I'm generating your video. This could take a few minutes."), false);

console.log("media capacity classification: ok");
