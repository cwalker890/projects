package edu.brandeis.services;

import com.google.common.collect.Lists;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import edu.brandeis.entities.Book;
import edu.brandeis.repos.BookRepository;

import java.util.List;

@Transactional
@Service("bookService")
public class BookServiceImpl implements BookService{

    private BookRepository bookRepository;
    @Override
	@Transactional(readOnly = true)
    public List<Book> findAll() {
        return Lists.newArrayList(bookRepository.findAll());
    }

    @Override
    @Transactional(readOnly = true)
    public Book findById(Long id) {
        return bookRepository.findById(id).get();
    }

    @Override
    public Book save(Book book) {
        return bookRepository.save(book);
    }

    @Autowired
    public void setBookRepository(BookRepository bookRepository){
        this.bookRepository = bookRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public Page<Book> findAllByPage(Pageable pageable) {
        return bookRepository.findAll(pageable);
    }
    
}