// Board interactions (SPEC §5.1): user columns drag by their handle; on
// drop the new order is posted as repeated column_ids fields. *Complete*
// sits outside the sortable list and always stays last (SPEC §11, Q1).
document.addEventListener("DOMContentLoaded", () => {
  const list = document.getElementById("user-columns");
  if (!list || typeof Sortable === "undefined") return;

  Sortable.create(list, {
    handle: ".column-handle",
    animation: 150,
    onEnd: () => {
      const ids = Array.from(list.querySelectorAll(".column")).map((el) =>
        el.dataset.columnId
      );
      const body = new URLSearchParams();
      for (const id of ids) body.append("column_ids", id);
      fetch(`/projects/${list.dataset.projectId}/columns/reorder`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });
    },
  });
});
