package handler

import (
	"encoding/json"
	"net/http"

	"gitstat/internal/store"
)

func ExportDataHandler(w http.ResponseWriter, r *http.Request) {
	repos := store.GlobalStore.GetRepositories()

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Content-Disposition", "attachment; filename=gitstat-data.json")
	json.NewEncoder(w).Encode(repos)
}
