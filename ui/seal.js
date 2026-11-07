// libsodium-compatible sealed box (crypto_box_seal), which GitHub requires for Actions secrets.
// sealed = ephemeral_pk || box(msg, nonce = blake2b(ephemeral_pk || recipient_pk, 24), recipient_pk, ephemeral_sk)
// Libraries are vendored (ui/vendor) so secrets never depend on a third-party CDN.
import "./vendor/nacl-fast.min.js";
import {blake2b} from "./vendor/blake2b.mjs";

export async function seal(value, keyB64) {
  const nacl = globalThis.nacl;
  const pk = Uint8Array.from(atob(keyB64), c => c.charCodeAt(0));
  const eph = nacl.box.keyPair();
  const nonceInput = new Uint8Array(64);
  nonceInput.set(eph.publicKey, 0);
  nonceInput.set(pk, 32);
  const nonce = blake2b(nonceInput, undefined, 24);
  const boxed = nacl.box(new TextEncoder().encode(value), nonce, pk, eph.secretKey);
  const out = new Uint8Array(32 + boxed.length);
  out.set(eph.publicKey, 0);
  out.set(boxed, 32);
  let bin = "";
  out.forEach(b => (bin += String.fromCharCode(b)));
  return btoa(bin);
}
