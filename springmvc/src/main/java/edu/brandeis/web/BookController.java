package edu.brandeis.web;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Locale;

import com.google.common.collect.Lists;
import org.apache.commons.io.IOUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.MessageSource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import edu.brandeis.entities.Book;

import edu.brandeis.services.BookService;
import edu.brandeis.util.UrlUtil;
import edu.brandeis.util.BookGrid;
import edu.brandeis.util.Message;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.Part;
import javax.validation.Valid;
@RequestMapping("/books")
@Controller
public class BookController {
    private final Logger logger = LoggerFactory.getLogger(BookController.class);

    private BookService bookService;
    private MessageSource messageSource;

    @RequestMapping(method = RequestMethod.GET)
    public String list(Model uiModel) {
        logger.info("Listing books");

        List<Book> books = bookService.findAll();
        uiModel.addAttribute("books", books);

        logger.info("No. of books: " + books.size());

        return "books/list";
    }

    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    public String show(@PathVariable("id") Long id, Model uiModel) {
        Book book = bookService.findById(id);
        uiModel.addAttribute("book", book);

        return "books/show";
    }

    @RequestMapping(value = "/{id}", params = "form", method = RequestMethod.POST)
    public String update(@Valid Book book, BindingResult bindingResult, Model uiModel,
                         HttpServletRequest httpServletRequest, RedirectAttributes redirectAttributes,
                         Locale locale) {
        logger.info("Updating book");
        if (bindingResult.hasErrors()) {
            uiModel.addAttribute("message", new Message("error",
                    messageSource.getMessage("book_save_fail", new Object[]{}, locale)));
            uiModel.addAttribute("book", book);
            return "books/update";
        }
        uiModel.asMap().clear();
        redirectAttributes.addFlashAttribute("message", new Message("success",
                messageSource.getMessage("book_save_success", new Object[]{}, locale)));
        bookService.save(book);
        return "redirect:/books/" + UrlUtil.encodeUrlPathSegment(book.getId().toString(),
                httpServletRequest);
    }

    @RequestMapping(value = "/{id}", params = "form", method = RequestMethod.GET)
    public String updateForm(@PathVariable("id") Long id, Model uiModel) {
        uiModel.addAttribute("book", bookService.findById(id));
        return "books/update";
    }

    // @RequestMapping(method = RequestMethod.POST)
    // public String create(@Valid Book book, BindingResult bindingResult, Model uiModel, HttpServletRequest httpServletRequest, RedirectAttributes redirectAttributes, Locale locale, @RequestParam(value="file", required=false) Part file) {
    //     logger.info("Creating book");
    //     if (bindingResult.hasErrors()) {
    //         uiModel.addAttribute("message", new Message("error",
    //                 messageSource.getMessage("book_save_fail", new Object[]{}, locale)));
    //         uiModel.addAttribute("book", book);
    //         return "books/create";
    //     }
    //     uiModel.asMap().clear();
    //     redirectAttributes.addFlashAttribute("message", new Message("success",
    //             messageSource.getMessage("book_save_success", new Object[]{}, locale)));

    //     logger.info("Book id: " + book.getId());

        // Process upload file
    //     if (file != null) {
    //         logger.info("File name: " + file.getName());
    //         logger.info("File size: " + file.getSize());
    //         logger.info("File content type: " + file.getContentType());
    //         byte[] fileContent = null;
    //         try {
    //             InputStream inputStream = file.getInputStream();
    //             if (inputStream == null) logger.info("File inputstream is null");
    //             fileContent = IOUtils.toByteArray(inputStream);
    //             book.setPhoto(fileContent);
    //         } catch (IOException ex) {
    //             logger.error("Error saving uploaded file");
    //         }
    //         singer.setPhoto(fileContent);
    //     }

    //     singerService.save(singer);
    //     return "redirect:/singers/";
    // }

    // @RequestMapping(value = "/photo/{id}", method = RequestMethod.GET)
    // @ResponseBody
    // public byte[] downloadPhoto(@PathVariable("id") Long id) {
    //     Book book = bookService.findById(id);

    //     if (book.getPhoto() != null) {
    //         logger.info("Downloading photo for id: {} with size: {}", book.getId(),
    //                 singer.getPhoto().length);
    //     }

    //     return singer.getPhoto();
    // }

//    @PreAuthorize("isAuthenticated()")
    @RequestMapping(params = "form", method = RequestMethod.GET)
    public String createForm(Model uiModel) {
        Book book = new Book();
        uiModel.addAttribute("book", book);

        return "books/create";
    }

    @ResponseBody
    @RequestMapping(value = "/listgrid", method = RequestMethod.GET, produces="application/json")
    public BookGrid listGrid(@RequestParam(value = "page", required = false) Integer page,
                                @RequestParam(value = "rows", required = false) Integer rows,
                                @RequestParam(value = "sidx", required = false) String sortBy,
                                @RequestParam(value = "sord", required = false) String order) {

        logger.info("Listing books for grid with page: {}, rows: {}", page, rows);
        logger.info("Listing books for grid with sort: {}, order: {}", sortBy, order);

        // Process order by
        Sort sort = null;
        String orderBy = sortBy;
        if (orderBy != null && orderBy.equals("title"))
            orderBy = "title";

        if (orderBy != null && order != null) {
            if (order.equals("desc")) {
                sort = new Sort(Sort.Direction.DESC, orderBy);
            } else
                sort = new Sort(Sort.Direction.ASC, orderBy);
        }

        // Constructs page request for current page
        // Note: page number for Spring Data JPA starts with 0, while jqGrid starts with 1
        PageRequest pageRequest = null;

        if (sort != null) {
            pageRequest = PageRequest.of(page - 1, rows, sort);
        } else {
            pageRequest = PageRequest.of(page - 1, rows);
        }

        Page<Book> bookPage = bookService.findAllByPage(pageRequest);

        // Construct the grid data that will return as JSON data
        BookGrid bookGrid = new BookGrid();

        bookGrid.setCurrentPage(bookPage.getNumber() + 1);
        bookGrid.setTotalPages(bookPage.getTotalPages());
        bookGrid.setTotalRecords(bookPage.getTotalElements());

        bookGrid.setBookData(Lists.newArrayList(bookPage.iterator()));

        return bookGrid;
    }

    @Autowired
    public void setBookService(BookService bookService) {
        this.bookService = bookService;
    }

    @Autowired
    public void setMessageSource(MessageSource messageSource) {
        this.messageSource = messageSource;
    }
}
