package edu.brandeis.util;

import java.util.List;

import edu.brandeis.entities.Book;

public class BookGrid {
    private int totalPages;
    private int currentPage;
    private long totalRecords;
    private List<Book> bookData;

    public int getTotalPages() {
        return totalPages;
    }

    public void setTotalPages(int totalPages) {
        this.totalPages = totalPages;
    }

    public int getCurrentPage() {
        return currentPage;
    }

    public void setCurrentPage(int currentPage) {
        this.currentPage = currentPage;
    }

    public long getTotalRecords() {
        return totalRecords;
    }

    public void setTotalRecords(long totalRecords) {
        this.totalRecords = totalRecords;
    }

    public List<Book> getBookData() {
        return bookData;
    }

    public void setBookData(List<Book> bookData) {
        this.bookData = bookData;
    }
}
