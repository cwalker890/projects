package edu.brandeis.repos;

import org.springframework.data.repository.PagingAndSortingRepository;

import edu.brandeis.entities.Book;

public interface BookRepository extends PagingAndSortingRepository<Book, Long>{
    
}