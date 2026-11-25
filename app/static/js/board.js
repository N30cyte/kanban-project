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
      ids.forEach((id) => body.append("column_ids", id));
      fetch(`/projects/${list.dataset.projectId}/columns/reorder`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });
    },
  });
});


// Card drag within / across columns (SPEC §5.1): SortableJS shared group; on
// drop the destination column's full card order is posted to /cards/move. *Complete*
// is never a drag target (SPEC §11, Q1).
document.addEventListener("DOMContentLoaded", () => {
  const lists = document.querySelectorAll(".cards");
  if (typeof Sortable === "undefined") return;

  lists.forEach((list) => {
    // *Complete* is locked: it renders outside #user-columns and is
    // never a drag destination (SPEC §11, Q1).
    if (!list.closest("#user-columns")) return;
    Sortable.create(list, {
      group: { name: "cards", pull: true, put: true },
      animation: 150,
      onEnd: (evt) => {
        const destination = evt.to || list;
        const columnEl = destination.closest(".column");
        const cards = Array.from(destination.querySelectorAll(".card"));
        const body = new URLSearchParams();
        body.append("card_id", evt.item.dataset.id);
        body.append("to_column_id", columnEl.dataset.columnId);
        cards.forEach((card) => body.append("card_ids", card.dataset.id));
        fetch("/cards/move", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: body.toString(),
        });
      },
    });
  });
});
