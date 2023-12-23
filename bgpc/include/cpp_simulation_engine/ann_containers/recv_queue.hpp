#ifndef RECV_QUEUE_HPP
#define RECV_QUEUE_HPP

#include <memory>
#include <vector>
#include <map>
#include <string>
#include "announcement.hpp"

class RecvQueue {
protected:
    std::map<std::string, std::vector<std::shared_ptr<Announcement>>> _info;

public:
    RecvQueue();

    void add_ann(const std::shared_ptr<Announcement>& ann);

    const std::map<std::string, std::vector<std::shared_ptr<Announcement>>>& prefix_anns() const;

    const std::vector<std::shared_ptr<Announcement>>& get_ann_list(const std::string& prefix) const;
};

#endif // RECV_QUEUE_HPP