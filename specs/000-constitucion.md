# 000 — Constitución del proyecto

- **Estado:** aprobada por Henry · aprobada por la compañera
- **Owner:** Ambos

Estos principios valen por encima de cualquier spec. Si una spec los contradice, gana la constitución.

1. **La experiencia gana votos.** La app debe ser divertida, rápida y clara para visitantes de colegio. Nada de pantallas técnicas en el modo feria.
2. **Local y privada.** Todo corre sin internet. No se identifica a nadie, y en la feria no se guardan fotos ni videos de visitantes. En los datasets las personas se llaman `P01`, `P02`, …
3. **Multiplataforma.** Kubuntu y la MacBook Pro M2 ejecutan el mismo código con Python ≥ 3.11 (probado con 3.14) y `pathlib`.
4. **Un conjunto acotado y ampliable de memes.** Son memes estáticos de TikTok (sobre todo de michis, pero no solo). Se empieza con los más fáciles de distinguir (ver `docs/memes.md`), más la clase `neutral`. Se pueden añadir más después, uno a la vez: recolectar sus datos, reentrenar y comprobar que la precisión no baja. En todo momento el conjunto es una lista cerrada y conocida: no se intenta reconocer cualquier meme.
5. **Landmarks, no píxeles.** Se clasifica con features geométricas y blendshapes normalizados, nunca con la imagen cruda.
6. **Spec antes que código, test antes que implementación.**
7. **`main` siempre funciona.** Se trabaja con PR pequeños, CI en verde y revisión cruzada.
8. **Honestidad del modelo.** Siempre se evalúa con personas no vistas. Si no hay confianza suficiente, se muestra "No estoy seguro".
9. **Nadie hace merge de código que ninguna de las dos personas entiende**, lo haya escrito una IA o no.
