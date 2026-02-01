async function enviar() {
  const numero = document.getElementById("numero").value;
  const modo = document.getElementById("modo").value;

  const res = await fetch("http://127.0.0.1:8000/spin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ numero: Number(numero), modo })
  });

  const data = await res.json();
  document.getElementById("resultado").innerText =
    JSON.stringify(data, null, 2);
}
